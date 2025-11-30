# Hangman: Hand-Gesture Controlled Version
This project is a hand gesture-controlled version of a hangman game I made for my CS class last year. It uses Python, OpenCV, and MediaPipe to detect your hand through the webcam, allowing you to select letters by hovering your fingertip over on-screen buttons, no mouse or keyboard needed.  

The game displays a full onscreen UI including a letter grid, category label, word progress, previously guessed letters, move counter, hover-based selection indicators, and a complete animated hangman drawing. A "play again" button appears at the end, also controlled by hover gestures.

## Installation
1. Clone this repository:
```
git clone https://github.com/shlokabhattacharyya/hangman-hand-gesture-control.git
cd hangman-hand-gesture-control
```
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Run the project:
```
python hangman.py
```
