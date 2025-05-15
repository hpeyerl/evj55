# EVJ55 Wiring

This will eventually contain the full wiring harness for my EVJ55 EV conversion project.  I hope to use large parts of the original harness for things like lighting, wipers, liftgate glass, etc.  I'll add in a custom relay box (probably from an old HDJ81 wiring harness I already have) as well as HF1A transfer case wiring for 4wd activation and sensors.

Wiring for the EV conversion will come from https://openinverter.org/wiki/Main_Page and indeed, many of the connector images all originate from that Wiki.

## Building.

In order to modularize this a bit with an eye to re-use by the community (hopefully),  and because YAML doesn't know about 'include' files, I've chosen to use the C-preprocessor and GnuMake. You will need a Linux system (or Windows WSL) to build it.  

You will also need to install Wireviz/Graphviz.

Instructions on how to do so are out of the scope of this document.

## Notes

I should probably split out the basic zombie.* files to a separate repository to make it easier for others to use without getting the rest of my EVJ55 junk.

* Backup light should be on a relay and come from Zombie ReverseLight output.

* Brake Light should be on a relay and come from both brake switch and Zombie BrakeLight (presumably for regen braking)

