'''
***********************************************************************

NOTES FOR STUDEENTS
-------------------
DO NOT MODIFY THIS FILE

***********************************************************************
'''

import pygame
import random
import socket
import threading
#from pygame_screen_record import ScreenRecorder

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 1000

# Port Listening
CONVEYOR_PORT = 12121
IMG_PORT = 12123

# Colors
SCREEN_BACKGROUND_WHITE = (255, 255, 255)
COOKIE_BROWN = (139, 69, 19)
DEVICES_GRAY = (120,120,120)
BELT_BLACK = (0,0,0)
TEXT_BLACK = (0,0,0)
CAMERA_AREA_RED = (200,0,0)

#Lists
BAD_COLORS = [(40,18,5), (70,20,15), (120,80,80)]
BAD_SHAPES = [(0,0,0), (1,2,15), (3,5,15), (4,6,20)]

#Object sizes
ARM_THICKNESS = 20
ARM_WIDTH = 150
BELT_WIDTH = 600
COOKIE_WIDTH = 100
COOKIE_QUALITY = 100 #between 10 and 100
ARM_POSITION = (SCREEN_WIDTH // 2) - ARM_WIDTH // 2
DEV_OFF_Y = SCREEN_HEIGHT // 2 - BELT_WIDTH // 2 - 10
CAM_MARGIN = COOKIE_WIDTH // 4
CAM_POSITION = COOKIE_WIDTH * 3 + CAM_MARGIN + 10
BELT_SPEED = 60 #between 30 and 300

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cookie Conveyor Belt Simulation")

class Arm:
    def __init__(self):
        self.y = DEV_OFF_Y - ARM_THICKNESS
        self.active = False
        self.speed = 0
        self.acceleration = 2
        # Counter for bad cookies and rejected
        self.rejectedCookies = 0

    def draw(self, screen):
        pygame.draw.rect(screen, DEVICES_GRAY, [ARM_POSITION, self.y, ARM_WIDTH, ARM_THICKNESS])
        pygame.draw.rect(screen, DEVICES_GRAY, [ARM_POSITION + (ARM_WIDTH // 2 - ARM_THICKNESS // 2), 
                                              self.y - ARM_WIDTH // 2, 
                                              ARM_THICKNESS, ARM_WIDTH // 2])


    def move(self):
        if self.active:
            self.speed += self.acceleration
            self.y += self.speed
            if self.y > SCREEN_HEIGHT // 2 + BELT_WIDTH // 2 + ARM_THICKNESS + 10:  # Arm is off the belt, return arm to original position
                self.active = False
                self.speed = 0
                self.y = DEV_OFF_Y - ARM_THICKNESS  # Reset arm position

    def push(self, cookies):
        if self.active:
            for cookie in cookies:
                if ARM_POSITION < cookie.x < ARM_POSITION + ARM_WIDTH and self.y + ARM_THICKNESS > cookie.y:
                    cookie.y = self.y  # Push the cookie to the right
                    if cookie.isBad and cookie.dead == False:
                        self.rejectedCookies += 1
                    cookie.dead = True
#-------------------------------------------------------------------------------------                    

class Cookie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dead = False
        self.bad = random.randint(0, COOKIE_QUALITY)
        self.isBad = 0<self.bad<4

        if self.bad == 1 or self.bad == 3:
            self.color = BAD_COLORS[random.randint(0,2)]
        else:
            self.color = COOKIE_BROWN

        if self.bad == 2 or self.bad ==3:
            self.shape_arc = BAD_SHAPES[random.randint(1,3)]
        else:
            self.shape_arc = BAD_SHAPES[0]
   
    def draw(self, screen):
        # Draw the full cookie
        pygame.draw.ellipse(screen, 
                            self.color, 
                            [self.x, self.y, COOKIE_WIDTH, COOKIE_WIDTH])

        # Draw the bite (an arc)
        pygame.draw.arc(screen,
                        (0,0,0), 
                        [self.x, self.y, COOKIE_WIDTH, COOKIE_WIDTH],
                        self.shape_arc[0], self.shape_arc[1], self.shape_arc[2])

    def move(self, speed):
        if(self.dead == False) :
            self.x += speed
#-------------------------------------------------------------------------------------

class Row:
    def __init__(self, rowNo):
        self.x = COOKIE_WIDTH // 2
        self.rowNo = rowNo

    def draw(self, screen):
        # Set up the font
        font = pygame.font.Font(None, 20)  # None uses the default font, 36 is the font size
        text = font.render(str(self.rowNo), True, TEXT_BLACK)
        # Blit the text onto the screen
        screen.blit(text, (self.x, SCREEN_HEIGHT // 2 + BELT_WIDTH // 2))  # Position the text at top

    def move(self, speed):
            self.x += speed
#-------------------------------------------------------------------------------------

class Belt:

    def draw(self, screen):
        pygame.draw.rect(screen, BELT_BLACK, [0, SCREEN_HEIGHT // 2 - BELT_WIDTH//2, SCREEN_WIDTH, BELT_WIDTH])
#-------------------------------------------------------------------------------------

class Camera:
    def __init__(self):
        self.capture_area = pygame.Rect(CAM_POSITION, SCREEN_HEIGHT // 2 - BELT_WIDTH // 2, 
                                        COOKIE_WIDTH + 15 , BELT_WIDTH)
        self.cam_poly = [(self.capture_area.left, DEV_OFF_Y),
                         (self.capture_area.left + CAM_MARGIN, DEV_OFF_Y - COOKIE_WIDTH),
                         (self.capture_area.left + (3 * CAM_MARGIN), DEV_OFF_Y - COOKIE_WIDTH),
                         (self.capture_area.left + COOKIE_WIDTH, DEV_OFF_Y)]

    def draw(self, screen):
        pygame.draw.rect(screen, CAMERA_AREA_RED, self.capture_area, 1)
        pygame.draw.polygon(screen, DEVICES_GRAY, self.cam_poly)
#-------------------------------------------------------------------------------------

class Listener:
    def __init__(self):
        self.stop_event = threading.Event()

    # Function to handle incoming socket connections
    def handle_arm_client(self, client_socket):
        #while not self.stop_event.is_set():
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message == "PUSH":
                pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN))
        except:
            pass
        client_socket.close()
    
    # Start a thread to handle incoming connections
    def start_arm_server(self, server):
        while not self.stop_event.is_set():
            try:
                client_socket, addr = server.accept()
                client_handler = threading.Thread(target=self.handle_arm_client, args=(client_socket,))
                client_handler.daemon = True
                client_handler.start()
            except:
                break

    def start_listening(self):
        # Set up the socket server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', CONVEYOR_PORT))
        server.listen(5)
        # Create a stop event
        server_thread = threading.Thread(target=self.start_arm_server, args=(server,))
        server_thread.daemon = True
        server_thread.start()
#-------------------------------------------------------------------------------------

class StatusMsg:
    def draw(self, screen, msg, coordinate):
        # Set up the font
        font = pygame.font.Font(None, 36)  # None uses the default font, 36 is the font size
        text = font.render(msg, True, TEXT_BLACK)
        # Blit the text onto the screen
        screen.blit(text, coordinate)  # Position the text at top
#-------------------------------------------------------------------------------------

class ScreenCapture:
    def __init__(self):
        self.imgCounter = -1

    def capture(self, screen, capture_area, analyze):
        if self.imgCounter>0: #cookie is in the range of camera
            capture_surface = screen.subsurface(capture_area)
            capture_image = pygame.Surface(capture_area.size)
            capture_image.blit(capture_surface, (0, 0))

            #pygame.transform.smoothscale(capture_image,)
            # Save the captured image
            imgFile = f"captures/image{self.imgCounter:02}.png"
            pygame.image.save(capture_image, imgFile)

            #only send image for analysis if opted
            if analyze:
                self.sendImage(imgFile)

        self.imgCounter += 1
        #storing only last 20 images
        if(self.imgCounter>IMG_LIMIT):
            self.imgCounter=1

    def sendImage(self, imgId):
        try:
            # Connect to the Pygame application
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', IMG_PORT))

            # Send a message to trigger a Pygame event
            client.send(f'FILE>{imgId}'.encode('utf-8'))
            client.close()
        except:
            print("** Analytic module not available")
#-------------------------------------------------------------------------------------

class Simulation:
    def __init__(self, shouldAnalyzeImg, imgLimit):
        self.shouldAnalyzeImg = shouldAnalyzeImg
        global IMG_LIMIT 
        IMG_LIMIT = imgLimit

    def start(self):
        clock = pygame.time.Clock()
        cookies = []
        rows = []
        speed = 2
        arm = Arm()
        belt = Belt()
        running = True
        stX = 0
        badCookies = 0
        rowNo = 1
        
        camera = Camera()
        listener = Listener()
        statusMsg = StatusMsg()
        screenCapture = ScreenCapture()

        listener.start_listening()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    listener.stop_event.set()
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    arm.active = True

            # Add a new cookies, only when the previous cookies have moved on enough
            if stX == 0:
                #add row
                rows.append(Row(rowNo))
                rowNo += 1
                if rowNo > IMG_LIMIT:
                    rowNo = 1

                stY = SCREEN_HEIGHT // 2 - BELT_WIDTH //2 + random.randint(0, COOKIE_WIDTH//2)
                #place cookies one below the other until the belt is full
                while stY <= SCREEN_HEIGHT // 2 + BELT_WIDTH //2 - COOKIE_WIDTH:
                    cookie = Cookie(random.randint(0, 10), stY)
                    #increment bad cookie counter
                    if cookie.isBad:
                        badCookies += 1
                    cookies.append(cookie)
                    stY += COOKIE_WIDTH + 5
            
            #Move the X pointer
            stX += speed
            if(stX > COOKIE_WIDTH + 10):
                stX = 0

            #draw scree
            screen.fill(SCREEN_BACKGROUND_WHITE)
            #draw the belt
            belt.draw(screen)

            # Move and draw cookies
            for cookie in cookies:
                cookie.move(speed)
                cookie.draw(screen)
            
            # Move and draw row
            for row in rows:
                row.move(speed)
                row.draw(screen)

            # Draw and move the arm
            arm.draw(screen)
            arm.move()
            arm.push(cookies)

            #draw camera and capture area
            camera.draw(screen)

            #draw the status text
            statusMsg.draw(screen, 
               f"Bad Cookies: {badCookies} | " + 
               f"Rejected Bad Cookies: {arm.rejectedCookies} " +
               f"(Efficiency: {(100 * float(arm.rejectedCookies) / float(badCookies) if badCookies > 0 else 0):.0f}%)",
               (0,0))

            # Remove cookies that have moved off the screen
            cookies = [cookie for cookie in cookies if cookie.x < SCREEN_WIDTH]
            rows = [row for row in rows if row.x < SCREEN_WIDTH]

            #-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
            if stX == 0:
                screenCapture.capture(screen, camera.capture_area, self.shouldAnalyzeImg)
            #-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

            pygame.display.flip()
            clock.tick(BELT_SPEED)
            
        pygame.quit()

