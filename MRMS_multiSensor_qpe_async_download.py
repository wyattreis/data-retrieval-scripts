# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
import os
import nest_asyncio
nest_asyncio.apply()
import asyncio
import aiohttp
import async_timeout


async def download_coroutine(url, session, destination):
    with async_timeout.timeout(1200):
        async with session.get(url) as response:
            if response.status == 200:
                fp = destination + os.sep + os.path.basename(url)
                with open(fp, 'wb') as f_handle:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f_handle.write(chunk)
            else:
                print(url)
            return await response.release()

async def main(loop, tmp, destination):

    async with aiohttp.ClientSession() as session:
        tasks = [download_coroutine(url, session, destination) for url in tmp]
        return await asyncio.gather(*tasks)


if __name__ == '__main__':

    start = datetime(2021, 10, 1, 0, 0)
    end = datetime(2021, 10, 2, 0, 0)
    destination = r"C:\workspace\ririe\HMS\data\precip"
    
    
    assert start >= datetime(2020,10,15), "MultiSensor MRMS data before 2020-10-15 does not exist, consider looking for GageCorr qpe grids"
    assert end >= datetime(2020,10,15), "MultiSensor MRMS data before 2020-10-15 does not exist, consider looking for GageCorr qpe grids"
    

    """
    https://inside.nssl.noaa.gov/mrms/past-code-updates/

    In the MRMS v12.0 update to NCO section, the third bullet from the bottom:
    -	Multi-sensor QPE scheme using gauges and model QPFs to fill radar coverage gaps
    I think that suggests the MultiSensor_QPE is gage corrected.  So the data might have just changed names in the MRMS migration to 12.0.
    """

    hour = timedelta(hours=1)
    os.makedirs(destination, exist_ok=True)
    
    #loop through and see if you already have the file locally
    date = start
    urls = []
    opath = []
    while date < end:
        
        url = 'https://mtarchive.geol.iastate.edu/{:04d}/{:02d}/{:02d}/mrms/ncep/MultiSensor_QPE_01H_Pass2/MultiSensor_QPE_01H_Pass2_00.00_{:04d}{:02d}{:02d}-{:02d}0000.grib2.gz'.format(
        date.year, date.month, date.day, date.year, date.month, date.day, date.hour)

        filename = url.split("/")[-1]
        if not os.path.isfile(destination + os.sep + filename):
            urls.append(url)
            opath.append(destination + os.sep + filename)
        date += hour

    #Split urls into chunks so you wont overwhelm IA mesonet with asyncronous downloads
    chunk_size = 50
    chunked_urls = [urls[i * chunk_size:(i + 1) * chunk_size] for i in range((len(urls) + chunk_size - 1) // chunk_size )]

    for tmp in chunked_urls:
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(main(loop, tmp, destination))
        del loop, results
