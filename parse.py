import cv2
import os


def video_parsing_second(file_name):

    video = cv2.VideoCapture(file_name)

    if not video.isOpened():
        print("Could not Open :", file_name)
        exit(0)
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)

     

    try:
        if not os.path.exists(r'C:\Users\ohs\Desktop\pycharm\label_able\privacy_video_annotation/2'):
            os.makedirs(r'C:\Users\ohs\Desktop\pycharm\label_able\privacy_video_annotation/2')
    except OSError:
        print('Error: Creating directory. ' + file_name[:-4])

    count = 0

    while (video.isOpened()):

        ret, image = video.read()
        # print(ret)
        # print(image)

        if not ret:
            break
        print(int(video.get(1)))
        if (int(video.get(1)) % 10 == 0):  # 앞서 불러온 fps 값을 사용하여 1초마다 추출
            print(file_name[:-4])
            # cv2.imshow('1', image)
            # cv2.waitKey(0)1

            cv2.imwrite(r'C:\Users\ohs\Desktop\pycharm\label_able\privacy_video_annotation\2' + "\\frame%d.jpg" % count, image)
            print('Saved frame number :', str(int(video.get(1))))
            count += 1

    video.release()

if __name__ == '__main__':
    video_parsing_second(r'C:\Users\ohs\Desktop\pycharm\label_able\privacy_video_annotation/20130421_183944.mp4')