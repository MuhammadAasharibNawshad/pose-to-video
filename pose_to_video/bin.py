#!/usr/bin/env python

import argparse
import importlib

import cv2
from pose_format.utils.generic import pose_normalization_info, correct_wrists, reduce_holistic
from pose_format.pose import Pose
from tqdm import tqdm


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pose', required=True, type=str, help='path to input pose file')
    parser.add_argument('--video', required=True, type=str, help='path to output video file')
    parser.add_argument('--type', required=True, type=str, choices=['pix2pix', 'mixamo', 'stylegan3'],
                        help='system to use')
    parser.add_argument('--model', required=True, type=str, help='model path to use')
    parser.add_argument('--upscale', action='store_true', help='should the output be upscaled to 768x768')

    return parser.parse_args()


def main():
    args = get_args()

    print('Loading input pose ...')
    with open(args.pose, 'rb') as pose_file:
        pose = Pose.read(pose_file.read())
        pose = reduce_holistic(pose)
        correct_wrists(pose)

    print('Generating video ...')


    video = None
    try:
        print(f"pose_to_video.conditional.{args.type}")
        module = importlib.import_module(f"pose_to_video.conditional.{args.type}")
    except ModuleNotFoundError:
        module = importlib.import_module(f"pose_to_video.unconditional.{args.type}")

    print('module', module)
    pose_to_video = module.pose_to_video
    frames: iter = pose_to_video(pose, args.model)

    if args.upscale:
        from pose_to_video.upscalers.simple import upscale
        frames = upscale(frames)

    for frame in tqdm(frames):
        if video is None:
            print('Saving to disk ...')
            height, width, _ = frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'MP4V')
            video = cv2.VideoWriter(filename=args.video,
                                    apiPreference=cv2.CAP_FFMPEG,
                                    fourcc=fourcc,
                                    fps=pose.body.fps,
                                    frameSize=(height, width))

        video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    video.release()


if __name__ == '__main__':
    main()
    # python bin.py --pose pix_to_pix/test.pose --video test.mp4 --model pix_to_pix
