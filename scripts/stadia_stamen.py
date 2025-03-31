"""
Usage:


Retrieves tiles from maps.stamen.com. Styles include terrain-background, terrain, toner and watercolor.
imagery = StadiaStamen('toner')


Documentation: https://stadiamaps.com/stamen/onboarding/migrate

* https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}{r}.png?api_key=
* https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png?api_key=
* https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.jpg?api_key=
* https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg?api_key=

Note: if you're using a library that doesn't support {r} (e.g., MapLibre), replace {r} with @2x or drop the placeholder to use standard 256x256 px tiles.

Attribution: 
&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a>
&copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a>
&copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a>
&copy; <a href="https://www.openstreetmap.org/copyright/" target="_blank">OpenStreetMap</a>

From https://stackoverflow.com/a/77825990
"""

import os
import cartopy.io.img_tiles as cimgt


class StadiaStamen(cimgt.Stamen):

    def _image_url(self, tile):
        stadia_api_key = os.environ.get('STADIA_API_KEY')
        x,y,z = tile
        r = '@2x'
        # url = f"https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png?api_key={stadia_api_key}"
        url = f'https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png?api_key={stadia_api_key}'
        return url

