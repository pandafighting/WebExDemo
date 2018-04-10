import cv2
import os
import re
import time
import tensorflow as tf
import numpy as np
import pkg_resources

import warnings
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"]="2"

from tesserocr import PyTessBaseAPI, RIL, PSM
from PIL import Image


def video_to_images(video_name, images_dir, window_size=1000):
    vidcap = cv2.VideoCapture(video_name)
    # success, image = vidcap.read()
    count = 0
    success = True
    window = 0

    while success:
        success, image = vidcap.read()
        vidcap.set(cv2.CAP_PROP_POS_MSEC, window)
        # print('Read a new frame: ', success)
        if success:
            cv2.imwrite(images_dir + 'frame%s.png' % f"{count:015b}", image)
            count += 1
        else:
            print("Found", count - 1, "frames")
        window += window_size


def remove_duplicates(images_path):
    image_filenames = [images_path + f for f in os.listdir(images_path) if os.path.join(images_path, f).endswith(".png")]

    def get_image_pixels_sum(image_path):
        image = cv2.imread(image_path, 0)
        return image.sum()

    previous_image = image_filenames[0]
    previous_image_sum = get_image_pixels_sum(previous_image)

    for frame_number in range(1, len(image_filenames)):
        current_image = images_path + 'frame' + f"{frame_number:015b}" + '.png'
        current_image_sum = get_image_pixels_sum(current_image)

        # optimize with map to get [true, false] then apply rm to list of duplicates

        if abs(previous_image_sum - current_image_sum) > 5500:
            os.system("rm '{}'".format(previous_image))
            
        previous_image = current_image
        previous_image_sum = current_image_sum


def crop_terminals(image_paths):
    MODEL_NAME = 'output_inference_graph.pb'
    PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
    PATH_TO_CKPT = pkg_resources.resource_filename(__name__, PATH_TO_CKPT)

    # Load a frozen Tensorflow model into memory.
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

    with detection_graph.as_default():
      with tf.Session(graph=detection_graph) as sess:
        # Definite input and output Tensors for detection_graph
        image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
        detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
        num_detections = detection_graph.get_tensor_by_name('num_detections:0')
        for image_path in image_paths:
            image = Image.open(image_path)
            (im_width, im_height) = image.size
            image_np = np.array(image.convert("RGB").getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)
            image_np_expanded = np.expand_dims(image_np, axis=0)
            # Actual detection.
            (boxes, scores, classes, num) = sess.run(
                [detection_boxes, detection_scores, detection_classes, num_detections],
                feed_dict={image_tensor: image_np_expanded})
            top_prediction = tuple(boxes[0].tolist())[0]
            # print(top_prediction)
            # print(100*scores[0][0])
            image_cropped = image.crop((int(top_prediction[1] * im_width),
                                        int(top_prediction[0] * im_height),
                                        int(top_prediction[3] * im_width),
                                        int(top_prediction[2] * im_height)))
            image_cropped.save(image_path)


def get_segments(image_dir):
    current_dir = image_dir[:-4] + '/'
    os.system("mkdir '{}'".format(current_dir))
    # print(image_dir)
    img = cv2.imread(image_dir, 0)
    height, width = img.shape
    img = cv2.resize(img, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    cv2.bitwise_not(img, img)
    # cv2.imwrite(image_dir, img)
    # image = Image.open(image_dir)
    image = Image.fromarray(img)
    with PyTessBaseAPI(psm=PSM.SINGLE_BLOCK) as api:
        api.SetImage(image)
        boxes = api.GetComponentImages(RIL.TEXTLINE, True)
        # print('Found {} textline image components.'.format(len(boxes)))
        for i, (im, box, _, _) in enumerate(boxes):
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
            cv2.imwrite('{}{}.png'.format(current_dir, f"{i:07b}"), img[box['y']:box['y'] + box['h'], box['x']:box['x'] + box['w']])


def quality_improve(image_dir):
    img = cv2.imread(image_dir, 0)
    # add denoising https://docs.opencv.org/3.0-beta/modules/photo/doc/denoising.html
    height, width = img.shape
    img = cv2.resize(img, (width * 5, height * 5), interpolation=cv2.INTER_CUBIC)
    mean = cv2.mean(img)[0]
    border_size = 10
    border = cv2.copyMakeBorder(img, top=border_size, bottom=border_size, left=border_size,
                                right=border_size, borderType=cv2.BORDER_CONSTANT, value=[mean, mean, mean])
    return border


def call_tesseract(cv_image, image_dir):
    pil_img = Image.fromarray(cv_image)
    with PyTessBaseAPI(psm=PSM.SINGLE_LINE) as api:
        api.SetImage(pil_img)
        ocr_result = api.GetUTF8Text()
        with open(image_dir[:-4] + ".txt", "w") as text_file:
            print(f"{ocr_result}", file=text_file)

                    
def join_txt_files(path):
    txt_filenames = [path + f for f in os.listdir(path) if os.path.join(path, f).endswith(".txt")]
    with open(path[:-1] + '.txt', 'w') as outfile:
        for txt_file in txt_filenames:
            with open(txt_file) as infile:
                for line in infile:
                    if not line.isspace():
                        outfile.write(line)
# !!!


def edit_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def glue_strings(s1, s2):
    MAX_THRESHOLD = 0.2
    first_run = True
    d = len(s2)

    while d > 0:
        i = len(s1) - d
        if i < 0:
            d -= 1
            continue

        cur_diff = edit_distance(s1[i: i + d], s2[0: d])

        if cur_diff <= MAX_THRESHOLD * d:
            return s1[0:len(s1) - d] + s2[0:d] if first_run else s1 + s2[d:]
        else:
            first_run = False
            step = max(int((cur_diff - MAX_THRESHOLD * d) / (2 - MAX_THRESHOLD)), 1)
            d -= step

    return s1 + s2


# Two lists are equal if *all* items at the same positions have "small" edit distance (< 20% length)
def check_equal_command_lists(list1, list2):
    if len(list1) != len(list2):
        return False

    MAX_THRESHOLD = 0.2
    for i in range(0, len(list1)):
        cur_dist = edit_distance(list1[i][1], list2[i][1])
        cmd_len = max(len(list1[i][1]), len(list2[i][1]))
        if cur_dist > MAX_THRESHOLD * cmd_len:
            return False
    return True


def glue_command_lists(list1, list2):
    first_run = True

    for d in range(len(list2), 0, -1):
        i = len(list1) - d
        if i < 0:
            continue

        offset = -1 if first_run and d > 1 else 0
        if check_equal_command_lists(list1[i: i + d + offset], list2[0: d + offset]):
            return list1[0:len(list1) - d] + list2
        first_run = False

    return list1 + list2


def read_file(path):
    myfile = open(path, "r")
    return "".join(myfile.readlines())


def extract_commands(path):
    file_names = [path + f for f in os.listdir(path) if os.path.join(path, f).endswith(".txt")]
    regexp = '[^ ]+#(.*)\n'
    all_commands = []
    for current_file in file_names:
        s = read_file(current_file)
        commands = [(int(''.join(re.findall('\d+', current_file.split('/')[-1])), 2), s.strip()) for s in re.findall(regexp, s)]
        commands = list(filter(lambda x: x[1] != 'I' and x[1] != '' and x[1] != "'", commands))
        commands = list(map(lambda x: (x[0], x[1].strip('I')), commands))
        commands = list(map(lambda x: (time.strftime('%H:%M:%S', time.gmtime(x[0])), x[1].strip('I')), commands))
        all_commands = glue_command_lists(all_commands, commands)
    return all_commands

# !!!


def get_transcript_commands(video_path):
    # print("Current video name: ", os.path.basename(video_path))
    images_path = os.path.dirname(video_path) + '/' + os.path.basename(video_path).split('.')[0]
    os.system("mkdir '{}'".format(images_path))
    images_path += '/'
    video_to_images(video_path, images_path)
    print("Converted video into images!")
    remove_duplicates(images_path)
    print("Removed duplicates!")
    frame_names = [images_path + f for f in os.listdir(images_path) if os.path.join(images_path, f).endswith(".png")]
    crop_terminals(frame_names)
    print("Cropped terminals!")
    for frame in frame_names:
        # print(frame)
        get_segments(frame)
        segments_dir = frame[:-4] + '/'
        current_segments = [segments_dir + f for f in os.listdir(segments_dir) if
                            os.path.join(segments_dir, f).endswith(".png")]
        for segment in current_segments:
            call_tesseract(quality_improve(segment), segment)
        join_txt_files(segments_dir)
    print("Got transcripts!")
    commands = extract_commands(images_path)
    print("Extracted commands!")
    # print(commands)
    os.system("rm -rf '{}'".format(images_path))
    return commands


def get_full_transcript(video_path):
    # print("Current video name: ", os.path.basename(video_path))
    print("Converting video into images...")
    images_path = os.path.dirname(video_path) + '/' + os.path.basename(video_path).split('.')[0]
    os.system("mkdir '{}'".format(images_path))
    images_path += '/'
    video_to_images(video_path, images_path)
    print("Removing duplicates...")
    remove_duplicates(images_path)
    frame_names = [images_path + f for f in os.listdir(images_path) if os.path.join(images_path, f).endswith(".png")]
    print("Cropping terminals...")
    crop_terminals(frame_names)
    print("Getting segments and transcripts...")
    for frame in frame_names:
        get_segments(frame)
        segments_dir = frame[:-4] + '/'
        current_segments = [segments_dir + f for f in os.listdir(segments_dir) if
                            os.path.join(segments_dir, f).endswith(".png")]
        for segment in current_segments:
            call_tesseract(quality_improve(segment), segment)
        join_txt_files(segments_dir)
    file_names = [images_path + f for f in os.listdir(images_path) if os.path.join(images_path, f).endswith(".txt")]
    full_transcript = read_file(file_names[0])
    for i in file_names[1:]:
        current_file = read_file(i)
        full_transcript = glue_strings(full_transcript, current_file)
    os.system("rm -rf '{}'".format(images_path))
    return full_transcript


def try_transcript_commands(video_path):
    try:
        commands = get_transcript_commands(video_path)
        return (0, commands)
    except:
        return (1, "error")
