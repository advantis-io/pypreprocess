import os
import joblib
import shutil
import commands

import numpy as np
import nibabel
from nisl import resampling


def is_3D(image_filename):
    return len(nibabel.load(image_filename).shape) == 3


def is_4D(image_filename):
    return len(nibabel.load(image_filename).shape) == 4


def get_vox_dims(volume):
    """
    Infer voxel dimensions of a nifti image.

    Parameters
    ----------
    volume: string
        image whose voxel dimensions we seek

    """

    print volume
    if not type(volume) is str:
        volume = volume[0]
    print volume
    nii = nibabel.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()

    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]


def delete_orientation(imgs, output_dir, output_tag=''):
    """
    Function to delete (corrupt) orientation meta-data in nifti.

    XXX TODO: Do this without using fsl

    """

    output_imgs = []
    if not type(imgs) is list:
        not_list = True
        imgs = [imgs]
    for img in imgs:
        output_img = os.path.join(
            output_dir,
            "deleteorient_%s_" % (output_tag) + os.path.basename(img))
        shutil.copy(img, output_img)
        print commands.getoutput(
            "fslorient -deleteorient %s" % output_img)
        print "+++++++Done (deleteorient)."
        print "Deleted orientation meta-data %s." % output_img
        output_imgs.append(output_img)

    if not_list:
        output_imgs = output_imgs[0]

    return output_imgs


def do_3Dto4D_merge(threeD_img_filenames):
    """
    This function produces a single 4D nifti image from several 3D.

    """

    if type(threeD_img_filenames) is str:
        return threeD_img_filenames

    output_dir = os.path.dirname(threeD_img_filenames[0])

    # prepare for smart caching
    merge_cache_dir = os.path.join(output_dir, "merge")
    if not os.path.exists(merge_cache_dir):
        os.makedirs(merge_cache_dir)
    merge_mem = joblib.Memory(cachedir=merge_cache_dir, verbose=5)

    # merging proper
    fourD_img = merge_mem.cache(nibabel.concat_images)(threeD_img_filenames)
    fourD_img_filename = os.path.join(output_dir,
                                      "fourD_func.nii")

    # sanity
    if len(fourD_img.shape) == 5:
        fourD_img = nibabel.Nifti1Image(
            fourD_img.get_data()[..., ..., ..., 0, ...],
            fourD_img.get_affine())

    merge_mem.cache(nibabel.save)(fourD_img, fourD_img_filename)

    return fourD_img_filename


def resample_img(input_img_filename,
                 new_vox_dims, output_img_filename=None):
    """Resamples an image to a new resolution

    Parameters
    ----------
    input_img_filename: string
        path to image to be resampled

    new_vox_dims: list or tuple of +ve floats
        new vox dimensions to which the image is to be resampled

    output_img_filename: string (optional)
        where output image will be written

    Returns
    -------
    output_img_filename: string
        where the resampled img has been written

    """

    # sanity
    if output_img_filename is None:
        output_img_filename = os.path.join(
            os.path.dirname(input_img_filename),
            "resample_" + os.path.basename(input_img_filename))

    # prepare for smart-caching
    output_dir = os.path.dirname(output_img_filename)
    cache_dir = os.path.join(output_dir, "resample_img_cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    mem = joblib.Memory(cachedir=cache_dir, verbose=5)

    # resample input img to new resolution
    resampled_img = mem.cache(resampling.resample_img)(
        input_img_filename,
        target_affine=np.diag(new_vox_dims))

    # save resampled img
    nibabel.save(resampled_img, output_img_filename)

    return output_img_filename
