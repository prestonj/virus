// virusRender - headless Access Virus TI renderer built on Gearmulator's virusLib.
//
// Boots the original TI firmware, loads a Single (from a .syx file or the ROM),
// plays a chord for a fixed time and writes the result to a 32-bit float WAV.
//
//   virusRender --rom rom/firmware.bin --list
//   virusRender --rom rom/firmware.bin --preset 0 --export-syx init.syx
//   virusRender --rom rom/firmware.bin --syx patch.syx --notes 48,55,60 --hold 2 --tail 2 --out out.wav

#include <atomic>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "dsp56kBase/semaphore.h"

#include "virusLib/device.h"
#include "virusLib/dspSingle.h"
#include "virusLib/microcontroller.h"
#include "virusLib/romfile.h"
#include "virusLib/romloader.h"

using namespace virusLib;
using namespace synthLib;

namespace
{
	constexpr size_t g_singleDumpSize = 524;

	struct Options
	{
		std::string rom;
		std::string syx;
		std::string preset;
		std::string out = "render.wav";
		std::string exportSyx;
		std::string dumpOut;
		std::vector<int> notes{60};
		int velocity = 100;
		double settle = 1.0;	// seconds between preset load and note on
		double hold = 2.0;
		double tail = 2.0;
		bool list = false;
	};

	void usage()
	{
		std::cerr <<
			"usage: virusRender --rom <firmware.bin> [options]\n"
			"  --list                 list ROM singles and exit\n"
			"  --preset <name|index>  use a ROM single (index = bank*128 + program)\n"
			"  --syx <file>           use a 524-byte Single Dump file\n"
			"  --export-syx <file>    write the selected single as .syx and exit\n"
			"  --notes 48,55,60       MIDI notes to hold (default 60)\n"
			"  --vel <1-127>          note velocity (default 100)\n"
			"  --settle <sec>         wait after loading before note on (default 1)\n"
			"  --hold <sec>           note length (default 2)\n"
			"  --tail <sec>           release time recorded after note off (default 2)\n"
			"  --out <file.wav>       output WAV (default render.wav)\n"
			"  --dump-out <file.syx>  save the edit buffer as the firmware holds it after loading\n";
	}

	bool parseArgs(const int _argc, char* _argv[], Options& _o)
	{
		for(int i = 1; i < _argc; ++i)
		{
			const std::string a = _argv[i];
			auto next = [&]() -> std::string
			{
				if(i + 1 >= _argc)
					throw std::runtime_error("missing value for " + a);
				return _argv[++i];
			};

			if(a == "--rom")				_o.rom = next();
			else if(a == "--syx")			_o.syx = next();
			else if(a == "--preset")		_o.preset = next();
			else if(a == "--out")			_o.out = next();
			else if(a == "--export-syx")	_o.exportSyx = next();
			else if(a == "--dump-out")		_o.dumpOut = next();
			else if(a == "--vel")			_o.velocity = std::stoi(next());
			else if(a == "--settle")		_o.settle = std::stod(next());
			else if(a == "--hold")			_o.hold = std::stod(next());
			else if(a == "--tail")			_o.tail = std::stod(next());
			else if(a == "--list")			_o.list = true;
			else if(a == "--notes")
			{
				_o.notes.clear();
				std::stringstream ss(next());
				std::string n;
				while(std::getline(ss, n, ','))
					_o.notes.push_back(std::stoi(n));
			}
			else
			{
				std::cerr << "unknown argument " << a << '\n';
				return false;
			}
		}
		return !_o.rom.empty();
	}

	uint8_t checksum(const std::vector<uint8_t>& _msg, const size_t _end)
	{
		// Virus checksum: sum of bytes from the device ID up to (excluding) _end
		uint32_t sum = 0;
		for(size_t i = 5; i < _end; ++i)
			sum += _msg[i];
		return static_cast<uint8_t>(sum & 0x7f);
	}

	bool loadSyx(const std::string& _file, std::vector<uint8_t>& _msg)
	{
		std::ifstream f(_file, std::ios::binary);
		if(!f)
		{
			std::cerr << "cannot open " << _file << '\n';
			return false;
		}
		_msg.assign(std::istreambuf_iterator<char>(f), {});

		if(_msg.size() != g_singleDumpSize || _msg[0] != 0xf0 || _msg[6] != DUMP_SINGLE || _msg.back() != 0xf7)
		{
			std::cerr << _file << " is not a 524-byte Virus TI Single Dump (" << _msg.size() << " bytes)\n";
			return false;
		}

		// Target the Single-mode edit buffer and accept any device ID
		_msg[5] = OMNI_DEVICE_ID;
		_msg[7] = 0x00;
		_msg[8] = SINGLE;

		const auto cs1 = checksum(_msg, 0x109);
		if(_msg[0x109] != cs1)
			std::cerr << "warning: first checksum was " << int(_msg[0x109]) << ", fixed to " << int(cs1) << '\n';
		_msg[0x109] = cs1;

		const auto cs2 = checksum(_msg, 0x20a);
		if(_msg[0x20a] != cs2)
			std::cerr << "warning: second checksum was " << int(_msg[0x20a]) << ", fixed to " << int(cs2) << '\n';
		_msg[0x20a] = cs2;
		return true;
	}

	bool findPreset(const ROMFile& _rom, const std::string& _name, ROMFile::TPreset& _out)
	{
		const bool isIndex = !_name.empty() && _name.find_first_not_of("0123456789") == std::string::npos;
		const int perBank = _rom.getPresetsPerBank();

		if(isIndex)
		{
			const int idx = std::stoi(_name);
			return _rom.getSingle(idx / perBank, idx % perBank, _out);
		}

		for(int b = 0; b < 26; ++b)
		{
			for(int p = 0; p < perBank; ++p)
			{
				ROMFile::TPreset data;
				if(!_rom.getSingle(b, p, data))
					return false;
				if(ROMFile::getSingleName(data) == _name)
				{
					_out = data;
					return true;
				}
			}
		}
		return false;
	}

	bool writeFile(const std::string& _file, const SysexBuffer& _data)
	{
		std::ofstream f(_file, std::ios::binary);
		f.write(reinterpret_cast<const char*>(_data.data()), static_cast<std::streamsize>(_data.size()));
		return static_cast<bool>(f);
	}

	bool writeWavFloat(const std::string& _file, const std::vector<float>& _interleaved, const uint32_t _samplerate)
	{
		std::ofstream f(_file, std::ios::binary);
		if(!f)
			return false;

		auto u32 = [&](uint32_t v) { f.write(reinterpret_cast<const char*>(&v), 4); };
		auto u16 = [&](uint16_t v) { f.write(reinterpret_cast<const char*>(&v), 2); };

		const uint32_t dataSize = static_cast<uint32_t>(_interleaved.size() * sizeof(float));
		f.write("RIFF", 4); u32(36 + dataSize); f.write("WAVE", 4);
		f.write("fmt ", 4); u32(16); u16(3 /* IEEE float */); u16(2); u32(_samplerate);
		u32(_samplerate * 2 * sizeof(float)); u16(2 * sizeof(float)); u16(32);
		f.write("data", 4); u32(dataSize);
		f.write(reinterpret_cast<const char*>(_interleaved.data()), dataSize);
		return static_cast<bool>(f);
	}

	float toFloat(const uint32_t _word)
	{
		// DSP output is 24-bit signed in the low bits of a 32-bit word
		const auto s = static_cast<int32_t>(_word << 8) >> 8;
		return static_cast<float>(s) / 8388608.0f;
	}
}

int main(const int _argc, char* _argv[])
{
	Options o;
	try
	{
		if(!parseArgs(_argc, _argv, o))
		{
			usage();
			return 1;
		}
	}
	catch(const std::exception& e)
	{
		std::cerr << e.what() << '\n';
		usage();
		return 1;
	}

	const ROMFile rom = ROMLoader::findROM(o.rom, DeviceModel::TI2);
	if(!rom.isValid())
	{
		std::cerr << "could not load TI ROM from " << o.rom << '\n';
		return 1;
	}

	if(o.list)
	{
		const int perBank = rom.getPresetsPerBank();
		for(int b = 0; b < 26; ++b)
		{
			for(int p = 0; p < perBank; ++p)
			{
				ROMFile::TPreset data;
				if(!rom.getSingle(b, p, data))
					return 0;
				const auto name = ROMFile::getSingleName(data);
				if(name.empty())
					return 0;
				std::printf("%4d  bank %2d prog %3d  %s\n", b * perBank + p, b, p, name.c_str());
			}
		}
		return 0;
	}

	ROMFile::TPreset romPreset{};
	std::vector<uint8_t> syx;

	if(!o.syx.empty())
	{
		if(!loadSyx(o.syx, syx))
			return 1;
	}
	else if(!findPreset(rom, o.preset.empty() ? "0" : o.preset, romPreset))
	{
		std::cerr << "preset '" << o.preset << "' not found in ROM\n";
		return 1;
	}

	if(!o.exportSyx.empty())
	{
		if(!syx.empty())
		{
			std::cerr << "--export-syx takes a ROM --preset, not --syx\n";
			return 1;
		}
		const auto dump = Microcontroller::createSingleDump(rom, BankNumber::EditBuffer, SINGLE, romPreset);
		if(!writeFile(o.exportSyx, dump))
			return 1;
		std::cout << "wrote " << ROMFile::getSingleName(romPreset) << " (" << dump.size() << " bytes) to " << o.exportSyx << '\n';
		return 0;
	}

	const uint32_t samplerate = rom.getSamplerate();

	DspSingle* dsp1Raw = nullptr;
	DspSingle* dsp2 = nullptr;
	virusLib::Device::createDspInstances(dsp1Raw, dsp2, rom, static_cast<float>(samplerate));
	std::unique_ptr<DspSingle> dsp1(dsp1Raw);

	auto uc = std::make_unique<Microcontroller>(*dsp1, rom, false);
	if(dsp2)
		uc->addDSP(*dsp2, false);

	const auto noteOnFrame = static_cast<uint64_t>(o.settle * samplerate);
	const auto noteOffFrame = noteOnFrame + static_cast<uint64_t>(o.hold * samplerate);
	const auto endFrame = noteOffFrame + static_cast<uint64_t>(o.tail * samplerate);

	// All timing is in ESAI callbacks counted on the DSP thread (one per output frame), so
	// events land on the same sample regardless of how the main thread is scheduled.
	constexpr uint64_t loadFrame = 256 * 4;	// preset load, as in Gearmulator's ConsoleApp
	const uint64_t onAt = loadFrame + noteOnFrame;
	const uint64_t offAt = loadFrame + noteOffFrame;
	const uint64_t endAt = loadFrame + endFrame;
	ROMFile::TPreset editBuffer{};
	std::atomic<bool> haveEditBuffer{false};

	const uint32_t blockSize = 64;
	const uint32_t notifyThreshold = blockSize - 4;
	int32_t notifyTimeout = 0;
	uint64_t callbackCount = 0;
	dsp56k::SpscSemaphore sem(1);
	std::vector<SMidiEvent> midiOut;
	std::vector<SMidiEvent> sysexResponses;

	auto sendNotes = [&](const uint8_t _status, const uint8_t _velocity)
	{
		for(const int n : o.notes)
			uc->sendMIDI(SMidiEvent(MidiEventSource::Host, _status, static_cast<uint8_t>(n), _velocity));
		uc->sendPendingMidiEvents(std::numeric_limits<uint32_t>::max());
	};

	// Called from the DSP thread every 4 ESAI callbacks, mirroring Gearmulator's ConsoleApp
	auto onTick = [&](const uint64_t _tick)
	{
		uc->process();

		if(_tick == 1)
		{
			dsp1->drainESSI1();
			uc->sendInitControlCommands(127);
		}
		else if(_tick * 4 == loadFrame)
		{
			dsp1->drainESSI1();
			dsp1->disableESSI1();
			if(!syx.empty())
				uc->sendSysex(SysexBuffer(syx.begin(), syx.end()), sysexResponses, MidiEventSource::Host);
			else
				uc->writeSingle(BankNumber::EditBuffer, SINGLE, romPreset);
		}
	};

	// Exact-frame note events, also on the DSP thread
	auto onFrame = [&](const uint64_t _frame)
	{
		if(_frame == onAt)
			sendNotes(0x90, static_cast<uint8_t>(o.velocity));
		else if(_frame == offAt)
		{
			sendNotes(0x80, 0x40);
			if(uc->requestSingle(BankNumber::EditBuffer, SINGLE, editBuffer))
				haveEditBuffer = true;
		}
	};

	auto& esai = dsp1->getAudio();
	esai.setCallback([&](dsp56k::Audio*)
	{
		const auto sizeReached = esai.getAudioOutputs().size() >= notifyThreshold;
		--notifyTimeout;
		if(notifyTimeout <= 0 && sizeReached)
		{
			notifyTimeout = static_cast<int32_t>(notifyThreshold);
			sem.notify();
		}

		uc->getMidiQueue(0).onAudioWritten();

		callbackCount++;
		onFrame(callbackCount);
		if((callbackCount & 0x3) == 0)
		{
			uc->readMidiOut(midiOut);
			midiOut.clear();
			onTick(callbackCount >> 2);
		}
	});

	virusLib::Device::bootDSPs(dsp1.get(), dsp2, rom, false);

	std::vector<uint32_t> outL(blockSize), outR(blockSize), inL(blockSize), inR(blockSize);
	TAudioInputsInt inputs{};
	TAudioOutputsInt outputs{};
	inputs[0] = inL.data();
	inputs[1] = inR.data();
	outputs[0] = outL.data();
	outputs[1] = outR.data();

	std::vector<float> recorded;
	recorded.reserve((endFrame - noteOnFrame) * 2);

	// Absolute output frame index; the main thread only records, it never triggers events
	uint64_t frame = 0;

	while(frame < endAt)
	{
		sem.wait();
		dsp1->processAudio(inputs, outputs, blockSize, blockSize);

		for(uint32_t i = 0; i < blockSize; ++i, ++frame)
		{
			if(frame >= onAt && frame < endAt)
			{
				recorded.push_back(toFloat(outL[i]));
				recorded.push_back(toFloat(outR[i]));
			}
		}
	}

	if(!writeWavFloat(o.out, recorded, samplerate))
	{
		std::cerr << "failed to write " << o.out << '\n';
		return 1;
	}

	float peak = 0.0f;
	for(const float s : recorded)
		peak = std::max(peak, std::abs(s));

	const auto name = haveEditBuffer ? ROMFile::getSingleName(editBuffer) : std::string("?");
	std::printf("rendered '%s' -> %s  (%.2fs, %u Hz, peak %.3f)\n", name.c_str(), o.out.c_str(),
		static_cast<double>(recorded.size() / 2) / samplerate, samplerate, peak);
	if(getenv("VIRUSRENDER_DEBUG"))
		std::printf("frames read %llu, ESAI callbacks %llu\n", static_cast<unsigned long long>(frame),
			static_cast<unsigned long long>(callbackCount));

	if(!o.dumpOut.empty() && haveEditBuffer)
	{
		const auto dump = Microcontroller::createSingleDump(rom, BankNumber::EditBuffer, SINGLE, editBuffer);
		if(writeFile(o.dumpOut, dump))
			std::cout << "edit buffer saved to " << o.dumpOut << '\n';
	}

	esai.setCallback([](dsp56k::Audio*) {});
	uc.reset();
	dsp1.reset();
	return 0;
}
