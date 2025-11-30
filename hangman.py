import random
import cv2
import mediapipe as mp
import numpy as np
import time

### game variables ###
words = {'animals': ['dolphin', 'penguin', 'turtle', 'giraffe', 'koala', 'otter', 'tiger', 'parrot'],
        'sports': ['soccer', 'basketball', 'baseball', 'football', 'tennis', 'hockey', 'lacrosse', 'swimming'],
        'fruits': ['apple', 'pineapple', 'banana', 'orange', 'grapes', 'pomegranate', 'cherry', 'mango'],
        'space': ['planets', 'constellation', 'asteroids', 'stars', 'rocket', 'galaxy', 'telescope', 'alien'],
        'superheroes': ['hulk', 'aquaman', 'wolverine', 'superman', 'flash', 'batman', 'ironman', 'spiderman'],
        'colors': ['red', 'purple', 'orange', 'pink', 'blue', 'yellow', 'green', 'black'],
        'languages': ['english', 'spanish', 'french', 'hindi', 'portuguese', 'russian', 'korean', 'mandarin']}

category = random.choice(list(words.keys()))
choice = random.choice(words[category])

word = list(choice)
status = ["_"] * len(word)
guessed = []
wrong = 0
moves = 0
buttons = {}
game_active = True
hover_start_time = {}
hover_letter = None
HOVER_DURATION = 1.0  # seconds to hover before selection
play_again_button = {'x': 300, 'y': 400, 'width': 200, 'height': 60}

### mediaoipe setup ###
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

### drawing functions ###
def draw_hangman_part(frame, part_num):
    """draw hangman parts on the frame"""
    color = (122, 65, 84)  # BGR for #54417a
    thickness = 4
    
    # calculate letter grid center to mirror position
    # letter grid is shifted 100px left from center, so shift hangman 100px right from mirror
    frame_center = 400  # half of 800px width
    letter_offset = -100  # letters are 100px left of center
    hangman_offset = 100  # mirror: 100px right of center
    
    # base position for hangman (mirrored on right side)
    base_x = 1050  # adjusted for symmetric placement
    base_y = 520
    
    if part_num >= 1:  # ground
        cv2.line(frame, (base_x - 75, base_y), (base_x + 75, base_y), color, thickness)
    if part_num >= 2:  # stand
        cv2.line(frame, (base_x, base_y), (base_x, base_y - 250), color, thickness)
        cv2.line(frame, (base_x, base_y - 250), (base_x + 75, base_y - 250), color, thickness)
        cv2.line(frame, (base_x + 75, base_y - 250), (base_x + 75, base_y - 195), color, thickness)
    if part_num >= 3:  # head
        cv2.circle(frame, (base_x + 75, base_y - 170), 25, color, thickness)
    if part_num >= 4:  # body
        cv2.line(frame, (base_x + 75, base_y - 145), (base_x + 75, base_y - 70), color, thickness)
    if part_num >= 5:  # left arm
        cv2.line(frame, (base_x + 75, base_y - 120), (base_x + 45, base_y - 90), color, 5)
    if part_num >= 6:  # right arm
        cv2.line(frame, (base_x + 75, base_y - 120), (base_x + 105, base_y - 90), color, 5)
    if part_num >= 7:  # left leg
        cv2.line(frame, (base_x + 75, base_y - 70), (base_x + 45, base_y - 30), color, thickness)
    if part_num >= 8:  # right leg
        cv2.line(frame, (base_x + 75, base_y - 70), (base_x + 105, base_y - 30), color, thickness)

def create_letter_buttons():
    """create button positions for all letters"""
    global buttons
    button_size = 40
    spacing = 10
    
    # calculate total grid dimensions
    buttons_per_row = 6
    total_rows = 5  # 26 letters / 6 per row ≈ 5 rows (last row has 2)
    grid_width = buttons_per_row * (button_size + spacing) - spacing
    grid_height = total_rows * (button_size + spacing) - spacing
    
    # center the grid horizontally and vertically between guessed text (y=115) and bottom
    # guessed text ends around y=115, so start centering from there
    available_height = 600 - 115  # space from guessed text to bottom
    y_start = 115 + (available_height - grid_height) // 2
    
    # center horizontally, but shift inward a bit (moved from edge)
    x_start = (800 - grid_width) // 2 - 150  # shifted 100px to the left
    
    x = x_start
    y = y_start
    
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        buttons[letter] = {
            'letter': letter,
            'x': x,
            'y': y,
            'size': button_size,
            'clicked': False
        }
        x += button_size + spacing
        if (i + 1) % 6 == 0:
            x = x_start
            y += button_size + spacing

def draw_buttons(frame, hover_info=None):
    """Draw all letter buttons on the frame with hover progress"""
    for letter, btn in buttons.items():
        if btn['clicked']:
            color = (128, 128, 128)  # gray for clicked buttons
        else:
            color = (114, 163, 219)  # orange/tan fill (BGR for #dba372)
        
        x, y, size = btn['x'], btn['y'], btn['size']
        cv2.rectangle(frame, (x, y), (x + size, y + size), color, -1)
        
        # draw hover progress indicator (gray filling from bottom)
        if hover_info and hover_info[0] == letter and hover_info[1] > 0:
            progress = hover_info[1]
            # draw gray progress bar filling from bottom
            progress_height = int(size * progress)
            cv2.rectangle(frame, (x, y + size - progress_height), (x + size, y + size), (180, 180, 180), -1)
        
        cv2.rectangle(frame, (x, y), (x + size, y + size), (122, 65, 84), 2)
        
        # draw letter
        text_size = cv2.getTextSize(letter, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = x + (size - text_size[0]) // 2
        text_y = y + (size + text_size[1]) // 2
        cv2.putText(frame, letter, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (122, 65, 84), 2)

def draw_game_info(frame):
    """draw category, word status, guessed letters, and moves"""
    h, w = frame.shape[:2]
    
    # category (center top, lower)
    category_text = f"category: {category}"
    cat_size = cv2.getTextSize(category_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)[0]
    cat_x = (w - cat_size[0]) // 2
    cv2.putText(frame, category_text, (cat_x, 50), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
    
    # word status (center)
    word_display = " ".join(status)
    word_size = cv2.getTextSize(word_display, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)[0]
    word_x = (w - word_size[0]) // 2
    cv2.putText(frame, word_display, (word_x, 85), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)
    
    # guessed letters (center)
    guessed_text = f"guessed: {', '.join(sorted(guessed))}"
    guessed_size = cv2.getTextSize(guessed_text, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)[0]
    guessed_x = (w - guessed_size[0]) // 2
    cv2.putText(frame, guessed_text, (guessed_x, 115), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    
    # moves (top right)
    cv2.putText(frame, f"moves: {moves}", (w - 120, 30), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)

def check_button_hover(x, y):
    """check if fingertip is hovering over a button and track hover time"""
    global hover_start_time, hover_letter
    
    current_time = time.time()
    
    # check which button is being hovered
    for letter, btn in buttons.items():
        if btn['clicked']:
            continue
        
        bx, by, size = btn['x'], btn['y'], btn['size']
        if bx <= x <= bx + size and by <= y <= by + size:
            # start tracking hover time for this letter
            if hover_letter != letter:
                hover_letter = letter
                hover_start_time[letter] = current_time
            
            # check if hover duration met
            hover_duration = current_time - hover_start_time.get(letter, current_time)
            if hover_duration >= HOVER_DURATION:
                hover_letter = None
                hover_start_time.clear()
                return letter, 1.0  # return letter and full progress
            
            return letter, hover_duration / HOVER_DURATION  # return letter and progress
    
    # not hovering over any button, reset
    hover_letter = None
    hover_start_time.clear()
    return None, 0.0

def process_guess(letter):
    """process a letter guess"""
    global guessed, status, wrong, moves, game_active
    
    if letter.lower() in guessed:
        return
    
    guessed.append(letter.lower())
    buttons[letter]['clicked'] = True
    
    if letter.lower() in word:
        for i in range(len(word)):
            if word[i] == letter.lower():
                status[i] = letter.lower()
    else:
        wrong += 1
    
    moves += 1
    
    if "_" not in status or wrong >= 8:
        game_active = False

def draw_game_over(frame):
    """draw game over screen"""
    overlay = frame.copy()
    
    if "_" not in status:
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (214, 190, 232), -1) 
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        text = "YOU WON!"
        color = (26, 92, 30)
    else:
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (222, 153, 106), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        text = "GAME OVER!"
        color = (57, 57, 196)

    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 2, 3)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = frame.shape[0] // 2 - 80
    cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 2, color, 3)
    
    word_text = f"the word was: {choice}"
    word_size = cv2.getTextSize(word_text, cv2.FONT_HERSHEY_DUPLEX, 1, 2)[0]
    word_x = (frame.shape[1] - word_size[0]) // 2
    word_y = text_y + 60
    cv2.putText(frame, word_text, (word_x, word_y), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
    
    # update play again button position to be below the text
    button_y = word_y + 60
    play_again_button['y'] = button_y

def draw_play_again_button(frame, hover_progress=0.0):
    """draw play again button with hover effect"""
    # center the button horizontally
    w = play_again_button['width']
    h = play_again_button['height']
    x = (frame.shape[1] - w) // 2  # center horizontally
    y = play_again_button['y']
    
    # update x position in the global button dict for hover detection
    play_again_button['x'] = x
    
    # button background
    button_color = (114, 163, 219)  # Orange (BGR for #dba372)
    cv2.rectangle(frame, (x, y), (x + w, y + h), button_color, -1)
    
    # hover effect - gray fill from bottom
    if hover_progress > 0:
        progress_height = int(h * hover_progress)
        cv2.rectangle(frame, (x, y + h - progress_height), (x + w, y + h), (180, 180, 180), -1)
    
    # button border
    cv2.rectangle(frame, (x, y), (x + w, y + h), (122, 65, 84), 3)
    
    # button text
    button_text = "play again!"
    text_size = cv2.getTextSize(button_text, cv2.FONT_HERSHEY_DUPLEX, 1, 2)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(frame, button_text, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 1, (122, 65, 84), 2)

def check_play_again_hover(x, y):
    """check if finger is hovering over play again button"""
    global hover_start_time, hover_letter
    
    current_time = time.time()
    bx, by = play_again_button['x'], play_again_button['y']
    bw, bh = play_again_button['width'], play_again_button['height']
    
    if bx <= x <= bx + bw and by <= y <= by + bh:
        # hovering over play again button
        if hover_letter != 'PLAY_AGAIN':
            hover_letter = 'PLAY_AGAIN'
            hover_start_time['PLAY_AGAIN'] = current_time
        
        hover_duration = current_time - hover_start_time.get('PLAY_AGAIN', current_time)
        if hover_duration >= HOVER_DURATION:
            hover_letter = None
            hover_start_time.clear()
            return True, 1.0  # button activated
        
        return False, hover_duration / HOVER_DURATION  # return progress
    
    # not hovering
    hover_letter = None
    hover_start_time.clear()
    return False, 0.0

### main game loop ###
def main():
    global game_active, wrong, moves, guessed, status, word, choice, category, buttons
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
    create_letter_buttons()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # process hand detection
        results = hands.process(rgb_frame)
        
        if game_active:
            # draw game elements
            draw_game_info(frame)
            
            hover_info = (None, 0.0)
            
            # process hand landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # draw hand skeleton
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # get index finger tip (landmark 8)
                    h, w, _ = frame.shape
                    finger_tip = hand_landmarks.landmark[8]
                    fx, fy = int(finger_tip.x * w), int(finger_tip.y * h)
                    
                    # draw finger position
                    cv2.circle(frame, (fx, fy), 10, (0, 255, 0), -1)
                    
                    # check for button hover
                    hover_info = check_button_hover(fx, fy)
                    if hover_info[0] and hover_info[1] >= 1.0:
                        process_guess(hover_info[0])
            
            draw_buttons(frame, hover_info)
            draw_hangman_part(frame, wrong)
        else:
            draw_game_over(frame)
            
            # check for play again button interaction
            play_again_hover = 0.0
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # draw hand skeleton
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # get index finger tip
                    h, w, _ = frame.shape
                    finger_tip = hand_landmarks.landmark[8]
                    fx, fy = int(finger_tip.x * w), int(finger_tip.y * h)
                    
                    # draw finger position
                    cv2.circle(frame, (fx, fy), 10, (0, 255, 0), -1)
                    
                    # check play again button
                    activated, progress = check_play_again_hover(fx, fy)
                    play_again_hover = progress
                    if activated:
                        # reset game
                        game_active = True
                        guessed.clear()
                        wrong = 0
                        moves = 0
                        hover_start_time.clear()
                        hover_letter = None
                        category = random.choice(list(words.keys()))
                        choice = random.choice(words[category])
                        word = list(choice)
                        status = ["_"] * len(word)
                        buttons.clear()
                        create_letter_buttons()
            
            draw_play_again_button(frame, play_again_hover)
        
        cv2.imshow('Hangman - Hand Gesture Control', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
