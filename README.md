# A Low-Cost, AI-Powered Safety Device to Prevent Child Hot Car Deaths

**Synopsys Science Fair 2024 — Project I48**
**Author:** Ajay Jagadish

---

## Overview

Every year, children die from heatstroke after being forgotten in hot cars. This project is a low-cost, standalone safety device that uses AI-powered object detection and a temperature sensor to detect when a child is left alone in an overheating vehicle and immediately sounds a loud alert — all without requiring any network connection.

The device runs entirely on a Raspberry Pi and can be mounted inside a car. It continuously monitors the vehicle interior, and if it detects a child alone under hot conditions, it plays a loud audio alert to draw attention.

---

## Engineering Goal

Design a low-cost safety device that can detect when a child is left alone in an overheated car and produce a sound alert, preventing child death.

---

## Design Criteria

| Requirement | Target |
|---|---|
| Detection field of view | 135 degrees |
| Child detection accuracy | At least 90% |
| Temperature monitoring threshold | 30°C (86°F) |
| Sound alert volume | At least 90 dB |
| Maximum device size | 10 cm x 20 cm x 6 cm |
| Maximum cost | $100 |
| Network connectivity | Not required |
| Minimum battery life | 8 hours |
| Processing platform | Raspberry Pi (real-time) |

---

## Hardware Components

- **Raspberry Pi** — central processor running all software in real-time
- **Raspberry Pi Camera Module** — captures video frames for object detection
- **DHT22 Temperature/Humidity Sensor** — reads ambient temperature inside the car
  - Data pin: GPIO 4
  - LED indicator: GPIO 16
  - Power pin: GPIO 8
- **Speaker** — plays the audio alert (connected as ALSA device `hw:2,0`)

---

## Software Architecture

### Main Application: [`hot_car.py`](hot_car.py)

The main loop runs continuously (every 60 seconds) and performs the following steps:

1. **Read temperature** from the DHT22 sensor via `pigpio` and the `DHT` driver
2. **Capture a video frame** from the Raspberry Pi camera using OpenCV
3. **Run object detection** using SSD MobileNet v3 (COCO model) to identify people in the frame
4. **Apply alert logic:**
   - If exactly **1 person** is detected (child alone, no adult present) **AND** temperature is **≥ 65°F (~18°C)**, play the audio alert
   - Otherwise, log the reading with no alert
5. **Log results** — saves each captured frame as a timestamped PNG and appends a line to `output/hot_car.out`

The single-person threshold is the key safety heuristic: if only one person is detected, it is assumed to be a child with no adult present. When two or more people are visible, an adult is likely in the car.

### Object Detection: [`Object_Detection_Files/`](Object_Detection_Files/)

- **Model:** SSD MobileNet v3 Large (COCO, January 2020)
  - Weights: `frozen_inference_graph.pb`
  - Config: `ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt`
- **Class labels:** `coco.names` (80 COCO classes; "person" class is used)
- **Input size:** 320x320, scaled to `[-1, 1]`
- **Confidence threshold:** 0.45
- **NMS threshold:** 0.2

### DHT22 Driver: [`DHT22.py`](DHT22.py)

A `pigpio`-based interrupt-driven driver for the DHT22 temperature and humidity sensor. Uses GPIO callbacks to decode the 40-bit serial protocol, with automatic power cycling on sensor hang.

---

## Alert Logic (Flowchart)

```
Initialize:
  person_threshold = 1
  temperature_threshold = 65°F

Loop forever:
  ┌─ Read temperature from DHT22
  ├─ Capture video frame from camera
  ├─ Run SSD MobileNet object detection
  ├─ Count detected persons (num_people)
  │
  ├─ IF num_people == 1 AND temp >= 65°F:
  │     → Play hot_car_alert.wav
  │     → Log: "PLAYING SOUND ALERT"
  │
  └─ ELSE:
        → Log: "NO ALERT"

  Sleep 60 seconds → repeat
```

---

## Test Plan

Tests were performed using a child-sized doll (decoy) placed in a car seat to simulate real-world scenarios.

| Test | Setup | Expected Result |
|---|---|---|
| 1 | 1 child decoy, car heated to ≥30°C, adult stepped out | Sound alert |
| 2 | 2 child decoys, car heated to ≥30°C, adult stepped out | Sound alert |
| 3 | 1 child decoy, car heated to ≥30°C, adult stays in car | No alert |
| 4 | 1 child decoy, comfortable temp (22°C), adult stepped out | Sound alert |
| 5 | 1 child decoy, comfortable temp (22°C), adult stays in car | No alert |
| 6 | 2 child decoys, comfortable temp (22°C), adult stepped out | Sound alert |

---

## Sample Output

From [`output/hot_car.txt`](output/hot_car.txt):

```
Children: 1    Temperature: 74.3 deg F    PLAYING SOUND ALERT
Children: 2    Temperature: 74.12 deg F   NO ALERT
Children: 1    Temperature: 89.42 deg F   PLAYING SOUND ALERT
Children: 1    Temperature: 95.18 deg F   PLAYING SOUND ALERT
Children: 4    Temperature: 107.78 deg F  NO ALERT
```

---

## Repository Structure

```
hotcar/
├── hot_car.py                        # Main application loop
├── DHT22.py                          # DHT22 temperature sensor driver
├── Object_Detection_Files/
│   ├── frozen_inference_graph.pb     # SSD MobileNet v3 model weights
│   ├── ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt  # Model config
│   ├── coco.names                    # COCO class labels
│   ├── object-ident.py               # Standalone object detection test scripts
│   ├── object-ident-2.py
│   ├── object-ident-3.py
│   ├── Identification_code.txt
│   └── Identification_code_original.txt
├── output/
│   ├── hot_car.txt                   # Device run log
│   ├── DHT.py                        # DHT sensor utility
│   └── *.png                         # Timestamped detection frames
├── hot_car_alert.wav                 # Primary alert audio
├── hot_car_alert_2.wav               # Alternate alert audio
├── I48-Research-Plan.docx            # Full research plan
├── I48-Research-Plan.pdf
├── I48.Abstract.pdf                  # Project abstract
├── Schematic 2024 - Ajay Jagadish.pptx  # Hardware schematic
├── Synopsys Science Fair Notes 2024.docx
├── IMG_9354.jpg                      # Prototype photos
├── IMG_9355.jpg
├── IMG_9357.jpg
├── IMG_9362.jpg
├── IMG_9365.jpg
└── IMG_9367.mov                      # Prototype demo video
```

---

## Dependencies

- Python 3
- [OpenCV](https://opencv.org/) (`cv2`) — video capture and object detection
- [pigpio](https://abyz.me.uk/rpi/pigpio/) — GPIO access for DHT22 sensor
- `aplay` (ALSA) — audio playback for the alert

Install on Raspberry Pi:
```bash
sudo apt-get install python3-opencv pigpio python3-pigpio alsa-utils
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

---

## Running the Device

```bash
# Start the pigpio daemon (required for DHT22)
sudo systemctl start pigpiod

# Run the main application
python3 hot_car.py
```

Output frames are saved to `output/` and the run log is appended to `output/hot_car.out`.

---

## References

1. Pratt, Michelle. *How to Prevent Hot Car Deaths.* Safe in the Seat. Dec. 13, 2023. https://safeintheseat.com/how-to-prevent-hot-car-deaths/
2. The Carlson Law Firm. *Forgotten Baby Syndrome: What it is and How to Avoid it.* June 6, 2023. https://www.carlsonattorneys.com/news-and-update/forgotten-baby-syndrome
3. Collins, Chris. *Set up temperature sensors in your home with a Raspberry Pi.* opensource.com. July 12, 2021.
4. Initial State. *Build an Inexpensive Network of Web-Connected Temperature Sensors using Pi Zeros.* Medium. Mar. 22, 2019.
5. Tim. *Object and Animal Recognition With Raspberry Pi and OpenCV.* Core Electronics. Feb. 16, 2023. https://core-electronics.com.au/guides/object-identify-raspberry-pi/
