import cv2 as cv
import numpy as np
from collections import defaultdict
import argparse, math


def tst():
    cap = cv.VideoCapture("volcano.mp4")

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
    font = "neuropol.ttf"
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
            threshold = 50
            contours = [x for x in all_contours if cv.contourArea(x) > threshold]
            srt = sorted(contours, key = cv.contourArea)
            if len(srt) > 0:
                lx,ly,lw,lh = cv.boundingRect(srt[0])
            blobs = 0
            id = 0
            prev = (WIDTH // 2, HEIGHT // 2)   #middle of frame
            #prev = (lx, ly)     
            #               #lines originate from largest blob
            seen = set()
            xs=[0] * len(contours)
            ys=[0] * len(contours)
            #print(xs)
            #print(ys)
            blob_data = []
            for contour in contours:
                #print(contour)
                area = cv.contourArea(contour)
                if area >= 1500 and area <= 2000:
                    cv.drawContours(frame, [contour], 0, (255, 255, 255), 1)    #-1 to fill
                    #opaque_overlay(frame, contour, (0,255,255))
                elif area <= 3000:
                    blobs+=1
                    x,y,w,h = cv.boundingRect(contour)
                    font_size = 1
                    #cv.putText(frame, str(blobs), (x, y+20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), font_size)
                    distance = math.dist((x, y), prev)
                    #print(f"distance: {distance}")
                    #draw_trajectory(frame, history, id)
                    #if (distance  > WIDTH / 4 or distance  > HEIGHT / 4 ):  
                    #    cv.line(frame, prev, (x, y), (255, 255, 255), 1)
                    #draw_trajectory(frame, history, id)
                    #prev = (x, y)
                    closest = find_closest(history, x, y, seen)
                    if not history[id] or closest == -1:
                        id +=1 
                    else:
                        id = closest
                    seen.add(id)
                    #print(f"id: {id} ")
                    #print(f"xs: {len(xs)}")
                    if id > len(contours): id-=((id - len(contours))+1)
                    xs[id-1] = x + (w // 2)
                    ys[id-1] = y + (h // 2)
                   # print(f"seen: {seen}")
                    #print(f'id:{id}')
                    #overlay = frame.copy()
                    #invert_blob_color(frame, contour)
                    #blur_blob(frame, contour, (20, 20))
                    cv.rectangle(frame,(x,y),(x+w,y+h),(255,255,255),1)    #-1 for fill
                    cv.putText(frame, str(id), ((x+w), y+(h//2)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), font_size)
                    #alpha = 1
                    #cv.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
                    history.setdefault(id, ([]))
                    history.setdefault(id, ([])).append((x, y+(h//2))) 
                    #draw_trajectory(frame, history, id)
                    data = f"x:{x} y:{y} id:{id}"
                    blob_data.append(data) 
            #connect_blobs(frame, contours, xs, ys)  
            #text_visuals(frame, blob_data, (0, 0, 255), HEIGHT)
            #blur_blob(frame, contour, (50,50))
            connect_blobs(frame, contours, xs, ys, (0, 0, 255))     
            output.write(frame)
        else:
            history = defaultdict(tuple)
    cv.destroyAllWindows() 
        
    cap.release()
    output.release()

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

def connect_blobs(frame, contours, xs, ys, color):
 
    distance_threshold = 149

    for i in range(len(contours)):
        for j in range(i+1, len(contours)):
            dx = xs[j] - xs[i]
            dy = ys[j] - ys[i]
            dist = np.sqrt(dx*dx + dy*dy)

            if dist < distance_threshold:
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
   tst()