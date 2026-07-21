import cv2 as cv
import numpy as np
from collections import defaultdict
import argparse, math, os


def main(input, lower_thresh, upper_thresh, color, fill, text, text_color, con, con_color, con_thresh, txt_visuals, tv_color, invert, blur, blur_amt, max_blobs):
    cap = cv.VideoCapture(input)

    if cap.isOpened():
        print("opened")
    else:
        print("Failure")

    WIDTH = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    HEIGHT = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    TOTAL_FRAMES = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    FPS = int(cap.get(cv.CAP_PROP_FPS))

    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    output = cv.VideoWriter("output.mp4", fourcc, FPS, (WIDTH, HEIGHT), isColor=True)
    history=defaultdict(tuple)
    frame_count=0
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_count+=1
        percent = int((frame_count / TOTAL_FRAMES) * 100)
        print(f"{frame_count} / {TOTAL_FRAMES}  ({percent}%)")
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)
        (all_contours, hierarchy) = cv.findContours(binary, cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        if len(all_contours)>0:
            lower_thresh
            contours = [x for x in all_contours if cv.contourArea(x) > lower_thresh and cv.contourArea(x) < upper_thresh]
            srt = sorted(contours, key = cv.contourArea) 
            id = 0
            seen = set()
            max_length = len(contours)
            if len(history) == 0 or len(contours) > max(history):
                max_length = len(contours)
            else:
                max_length=max(history)
            xs=[0] * max_length
            ys=[0] * max_length
            blob_data = []   
            if(len(contours) > max_blobs): contours = contours[0:max_blobs]
            for contour in contours:
                area = cv.contourArea(contour)
                x,y,w,h = cv.boundingRect(contour)
                closest = find_closest(history, x, y, seen)
                if not history[id] or closest == -1:
                    id +=1 
                else:
                    id = closest
                seen.add(id)
                if id > len(xs): 
                    xs.append(0)
                    ys.append(0)
                cv.rectangle(frame,(x,y),(x+w,y+h), color, fill)    #-1 for fill
                if text == 0:
                     cv.putText(frame, str(id), ((x+(w//2)), y+((h//2)+h)), cv.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
                if text == 1:
                     cv.putText(frame, f"x: {x}", (x, y+h+10), cv.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
                     cv.putText(frame, f"y: {y}", (x, y+h+20), cv.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
                         
                history.setdefault(id, ([]))
                history.setdefault(id, ([])).append((x, y+(h//2)))
                if invert:
                    invert_blob_color(frame, contour)
                elif blur:
                    blur_blob(frame, contour, blur_amt)
                data = f"x:{x} y:{y} id:{id}"
                blob_data.append(data)    
            if con:
                connect_blobs(frame, contours, xs, ys, con_color, con_thresh)
            if txt_visuals:
                text_visuals(frame, blob_data, text_color, HEIGHT)
        output.write(frame)



                



def draw_trajectory(frame, history, id):
    points = history.get(id)
    if len(points) < 2: return
    start_point = 0
    if len(points) > 10:
        start_point=len(points) -5
    for i in range(start_point, len(points)-1):
        cv.line(frame, points[i], points[i+1], (255, 255, 255), 1)

def draw_lines_from_center(frame, contours, WIDTH, HEIGHT): #put in WIDTH and HEIGHT of frame
    centr = (WIDTH // 2, HEIGHT // 2)
    for contour in contours:
        x,y,w,h = cv.boundingRect(contour)
        cv.line(frame, centr, (x, y), (255,255,255), 1, cv.LINE_8)



def find_closest(history, x, y, seen):    
    closest = None
    ret = -1
    if len(history) == 0:
        return -1
    for id in history:
        points = history.get(id)
        #print(points)
        if len(points) == 0: continue
        point = points[-1] #get last point of contour
        #print(f"point: {point}")
        dist = math.dist((x, y), point)
        if not closest: 
            closest = dist
            continue        
        if dist < closest: 
            closest = dist
            ret = id
    if ret in seen:
        ret = max(seen) + 1
    return ret


def invert_blob_color(frame, contour): 
    x, y, w, h = cv.boundingRect(contour)
    range = frame[y:y+h, x:x+w]
    invrt = cv.bitwise_not(range)
    frame[y:y+h, x:x+w,:] = invrt
    
    
def opaque_overlay(frame, contour, color):
    alpha = 0.2
    overlay = frame.copy()
    cv.drawContours(overlay, [contour], 0, color, thickness=-1)
    cv.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

def zoom_blob(frame, contour, zoom_factor):
    return

def connect_blobs(frame, contours, xs, ys, color, thresh):

    for i in range(len(contours)):
        for j in range(i+1, len(contours)):
            if xs[i] == 0 or ys[i] == 0: continue
            dx = xs[j] - xs[i]
            dy = ys[j] - ys[i]
            dist = np.sqrt(dx*dx + dy*dy)

            if dist < thresh:
                point1 = (xs[i], ys[i])
                point2 = (xs[j], ys[j])

                cv.line(frame, point1, point2, color, 1, cv.LINE_4)
    return


def blur_blob(frame, contour, ksize):
    x, y, w, h = cv.boundingRect(contour)
    range = frame[y:y+h, x:x+w]
    invrt = cv.blur(range, ksize)
    frame[y:y+h, x:x+w,:] = invrt


def text_visuals(frame, data, color, height):
    y = 20
    for d in data:
        cv.putText(frame, d, (10, y), cv.FONT_HERSHEY_SIMPLEX,0.5, color, 1)
        y+=20
        if y >= height:
            break

def curved_lines(frame):
    return



if __name__=="__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--input", required = True, help="input video file, will be written to output.mp4. example usage: --input file.mp4")
   parser.add_argument("--lower_thresh", default = 0, help="area threshold to recognize a blob. example usage: --thresh", type = int)
   parser.add_argument("--upper_thresh", default = 2147483647, help="area threshold to recognize a blob. example usage: --thresh", type = int)
   parser.add_argument("--blob_color", default = (255,255,255), nargs = 3, help="BGR format blob marking rectangle color . example usage: --blob_color 255 255 255", type = int)
   parser.add_argument("--fill", default = 1, help="rectangle fill (1 for no fill, -1 to fill). example usage: --fill 1")
   parser.add_argument("--txt_id", default = False, action = 'store_true',help="display information next to blobs (id)")
   parser.add_argument("--txt_xy", default = True, action = 'store_true',help="display information next to blobs (coordinates)")
   parser.add_argument("--txt_col", default = (255,255,255), nargs = 3, help="BGR format color of text. example usage", type = int)
   parser.add_argument("--connections", action = 'store_true', default = True, help="draw connection networks between blobs")
   parser.add_argument("--con_color", default = (255, 255, 255), nargs = 3, help="BGR format color of connection lines. example usage: --con_color 255 255 255", type = int) 
   parser.add_argument("--con_thresh", default = 200, help="pixel distance threshold for drawing connection lines. example usage: --con_thresh 200", type = int)
   parser.add_argument("--txt_visuals", action = 'store_true', default = False, help="add text visuals in top left of screen")
   parser.add_argument("--tv_color", default = (255, 255, 255), nargs = 3, help="BGR format text color for text visuals. example usage: --tv_color 255 255 255", type = int)
   parser.add_argument("--invert", default = False, action = 'store_true', help="invert color within blobs")
   parser.add_argument("--blur", default = False, action = 'store_true', help="blur blobs")
   parser.add_argument("--blur_amt", default = (10,10), nargs = 2, help = "(blur kernel size. larger ksize = stronger blur). example usage: --blur_amt 10 10", type = int)
   parser.add_argument("--max_blobs", default = 2147483647, help="maximum amount of blobs per frame", type = int)
   args = parser.parse_args()

   args.blob_color = tuple(args.blob_color)
   print(args.blob_color)
   args.txt_color = tuple(args.txt_col)
   args.connections_color = tuple(args.con_color)
   args.blur_amt = tuple(args.blur_amt)
   txt = -1 
   if args.txt_id:
       txt = 0
   elif args.txt_xy:
       txt = 1      
   main(args.input, args.lower_thresh, args.upper_thresh, args.blob_color, args.fill, txt, args.txt_col, args.connections, args.con_color, args.con_thresh, args.txt_visuals, args.tv_color, args.invert, args.blur, args.blur_amt, args.max_blobs)