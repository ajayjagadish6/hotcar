import board
import cv2
import pigpio
import DHT
import time
import subprocess

#thres = 0.45 # Threshold to detect object
person_threshold = 1 # number of persons
temperature_threshold = 65 # in degree fahrenheit

classNames = []
classFile = "/home/pi/synopsys_2024/Object_Detection_Files/coco.names"
with open(classFile,"rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

configPath = "/home/pi/synopsys_2024/Object_Detection_Files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "/home/pi/synopsys_2024/Object_Detection_Files/frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath,configPath)
net.setInputSize(320,320)
net.setInputScale(1.0/ 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)


def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img,confThreshold=thres,nmsThreshold=nms)
    #print(classIds,bbox)
    if len(objects) == 0: objects = classNames
    objectInfo =[]
    if len(classIds) != 0:
        for classId, confidence,box in zip(classIds.flatten(),confs.flatten(),bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box,className])
                if (draw):
                    cv2.rectangle(img,box,color=(0,255,0),thickness=2)
                    cv2.putText(img,classNames[classId-1].upper(),(box[0]+10,box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
                    cv2.putText(img,str(round(confidence*100,2)),(box[0]+200,box[1]+30),
                    cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)

    return img,objectInfo

def output(message):
	file1 = open("/home/pi/synopsys_2024/output/hot_car.out", "a")
	file1.write(message)
	file1.write("\n")
	file1.close()

if __name__ == "__main__":

	while True:

		#First, read the temperature from the DHT sensor
		# Intervals of about 2 seconds or less will eventually hang the DHT22.
		INTERVAL=3
		pi = pigpio.pi()
		s = DHT.sensor(pi, 4, LED=16, power=8)
		next_reading = time.time()

		temp_c = 0
		while temp_c == 0:
			s.trigger()
			time.sleep(0.2)
			temp_c = s.temperature()
			next_reading += INTERVAL
			time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.

		s.cancel()
		pi.stop()
		#temp_f = format(temp_c * 9.0/5.0 + 32.0, ".2f")
		temp_f = temp_c * 9.0/5.0 + 32.0


		#Read a video frame from the raspberry pi camera
		cap = cv2.VideoCapture(0)
		cap.set(3,640)
		cap.set(4,480)
		#cap.set(10,70)
		#Identify all objects in the video frame 
		success, img = cap.read()
		result, objectList = getObjects(img,0.45,0.2)
		#print(objectList)
		cap.release()

		num_people = 0
		for obj in objectList:
			thing = obj[1]
			# print('Found: ',thing)
			if thing == 'person':
				num_people = num_people + 1

		#print('Number of people detected: ', num_people)
		#print('Temperature: ' ,temp_f, 'deg F')
		#cv2.imshow("Output",img)
		#cv2.waitKey(0)

		img_filename = "/home/pi/synopsys_2024/output/" + str(int(time.time())) + ".png"
		cv2.imwrite(img_filename, img)

		if num_people == person_threshold and temp_f >= temperature_threshold:
			result = subprocess.Popen(["/usr/bin/aplay", "-D", "hw:2,0", "/home/pi/synopsys_2024/hot_car_alert.wav"])
			output("Children: {persons}	Temperature: {temp} deg F  PLAYING SOUND ALERT".format(persons = num_people, temp = temp_f))
		else:
			output("Children: {persons}	Temperature: {temp} deg F  NO ALERT".format(persons = num_people, temp = temp_f))

		time.sleep(60)