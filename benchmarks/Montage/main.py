import os
import sys
import shutil
import json

from MontagePy.main    import *
from MontagePy.archive import *


location = 'M31'
dataset = 'WISE W1'
size = 2.0
outfile='band1.fits'
verbose = True

resolution         = 1
coordinateSystem   = 'Equatorial'
workdir            = "work"
backgroundMatching = True


# Arguments
if dataset[:4].upper() == 'WISE':
    resolution = 6.0
if dataset[:4].upper() == 'SDSS':
    resolution = 0.4

home = os.getcwd()
os.chdir(home)

# Clean out any old copy of the work tree, then remake it
# and the set of the subdirectories we will need.

try:
    shutil.rmtree(workdir)
except:
    pass

os.makedirs(workdir)

os.chdir(workdir)

os.makedirs("raw")
os.makedirs("projected")
os.makedirs("diffs")
os.makedirs("corrected")

# Create the FITS header for the mosaic.

print("Constructing region header specification ...")
if verbose == False:
    clear_output(wait=True)

status = mHdr(location, size, size, "region.hdr",
                   resolution=resolution, csys=coordinateSystem)

if status['status'] == 1:
    print(status['msg'])
    exit(1)

# Retrieve archive images covering the region then scan
# the images for their coverage metadata.

print("Downloading image data ...")
if verbose == False:
   clear_output(wait=True)

status = mArchiveDownload(dataset, location, size, "raw")

status = status.replace("'", '"')         # Kludge around a bug
status = json.loads(status)               # in MontagePy code

if status['status'] == 1:
    print(status['msg'])
    exit(1)

print("Collecting metadata for " + str(status['count']) + " images ...")
if verbose == False:
    clear_output(wait=True)

status = mImgtbl("raw", "rimages.tbl")

if status['status'] == 1:
    print(status['msg'])
    exit(1)

# Reproject the original images to the  frame of the
# output FITS header we created

print("Reprojecting images ...")
if verbose == False:
    clear_output(wait=True)

status = mProjExec("raw", "rimages.tbl", "region.hdr", projdir="projected", quickMode=True)

if status['status'] == 1:
    print(status['msg'])
    exit(1)

print("Collecting projected image metadata ...")
if verbose == False:
    clear_output(wait=True)

mImgtbl("projected", "pimages.tbl")

if status['status'] == 1:
    print(status['msg'])
    exit(1)

if backgroundMatching:
    # Determine the overlaps between images (for background modeling).
    print("Determining image overlaps for background modeling ...")
    if verbose == False:
        clear_output(wait=True)

    status = mOverlaps("pimages.tbl", "diffs.tbl")

    if status['status'] == 1:
        print(status['msg'])
        exit(1)

    # Generate difference images and fit them.
    print("Analyzing " + str(status['count']) + " image overlaps ...")
    if verbose == False:
        clear_output(wait=True)

    status = mDiffFitExec("projected", "diffs.tbl", "region.hdr", "diffs", "fits.tbl")

    if status['status'] == 1:
        print(status['msg'])
        exit(1)

    # Model the background corrections.
    print("Modeling background corrections ...")
    if verbose == False:
        clear_output(wait=True)

    status = mBgModel("pimages.tbl", "fits.tbl", "corrections.tbl")

    if status['status'] == 1:
        print(status['msg'])
        exit(1)


    # Background correct the projected images.
    print("Applying background corrections ...")
    if verbose == False:
        clear_output(wait=True)

    status = mBgExec("projected", "pimages.tbl", "corrections.tbl", "corrected")

    if status['status'] == 1:
        print(status['msg'])
        exit(1)


    print("Collecting corrected image metadata ...")
    if verbose == False:
        clear_output(wait=True)

    status = mImgtbl("corrected", "cimages.tbl")

    if status['status'] == 1:
        print(status['msg'])
        exit(1)

    # Coadd the background-corrected, projected images.
    os.chdir(home)

    print("Coadding corrected images into final mosaic ...")
    if verbose == False:
        clear_output(wait=True)

    status = mAdd(workdir+"/corrected", workdir+"/cimages.tbl", workdir+"/region.hdr", outfile)

    if status['status'] == 1:
        print(status['msg'])
        exit(1)
else:
    # Coadd the projected images.
    os.chdir(home)

    print("Coadding projected images into final mosaic ...")
    if verbose == False:
        clear_output(wait=True)

    status = mAdd(workdir+"/projected", workdir+"/pimages.tbl", workdir+"/region.hdr", outfile)

    if status['status'] == 1:
        print(status['msg'])
        exit(1)

print("Final mosaic image: " + outfile)
