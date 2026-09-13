#!/bin/bash
# Run this from inside the sumo_net folder.
# netconvert compiles the .nod.xml and .edg.xml files into one usable .net.xml network file.
# Because J001 is marked type="traffic_light" in the nodes file, netconvert automatically
# generates a default traffic light program (phases) for it -- this becomes your starting
# fixed-time baseline, which you can inspect/edit afterward in netedit or by hand.

netconvert \
  --node-files=intersection.nod.xml \
  --edge-files=intersection.edg.xml \
  --output-file=intersection.net.xml \
  --tls.guess-signals true \
  --tls.default-type static

echo "Done. intersection.net.xml has been created."
echo "Open it visually with: sumo-gui -n intersection.net.xml"
