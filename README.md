# ipTIME Utilities

## Configuration File Extraction/Re-packing

The python script `ipTIME_config.py` can extract/re-pack the configuration backup file downloaded from the ipTIME
router's web interface (tested on n704).

Example:

```bash
$ python ipTIME_config.py -e config_n704v3_20000101_010901.cfg
PoC for extracting/repacking ipTIME backup configuration file
Warning: only tested on ipTIME n704 v3, firmware version 9.98.6
Extracting ipTIME configuration...
	[+] Extracting outer gzip
	[+] Dumping extracted header
		Magic: raw_nv
		Size of gz (compressed): 3183
		Sum of gz bytes: 0x677A4
		Max size: 32720
		FS id: 0x10000
	[+] Extracting inner tar.gz tarball
Extraction successful. You can now edit configuration files in ./etc/
Use -c to pack the new configuration
```

You can then edit any of the configuration files from `./etc/`, such as `./etc/init.d/rcS` for instance and re-pack the
configuration file.

```bash
$ python ipTIME_config.py -c newconf.cfg
PoC for extracting/repacking ipTIME backup configuration file
Warning: only tested on ipTIME n704 v3, firmware version 9.98.6
Packing new configuration files...
	[+] Create tarball of ./etc/
	[+] Generating new ipTIME header
		Computed sum: 0x67772
	[+] Creating outer gzip file
Packing successful. You can now upload the configuration file to ipTIME router.
```
