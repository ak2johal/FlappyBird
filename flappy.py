#AK: Importing necessary python modules required for the game to handle graphics, sounds, numbers and all other required functions. 
import random
import sys
from itertools import cycle

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP

#AK: This is the display settings for the game such as, screenwidth and screenheight. The values set the size of the display window to control what exactly the player sees. 
FPS = 60
SCREENWIDTH = 288
SCREENHEIGHT = 512
#AK: The distance between the lower and upper pipe, controlling how the overall difficulty of the game as well. 
PIPEGAPSIZE = 100
#AK: This is where the bottom/grass is located on the screen so that the bird knows where the gradd is located if it falls. 
BASEY = int(SCREENHEIGHT * 0.79)


#AK: This is the dictionary for images, sound and hitmask variables in one place for easy access 
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

#AK: This turns the sounds on and off incase the system doesn't play it on its own 
ENABLE_SOUNDS = True

#AK: This ensures xrange is compatible with Python 2 & Python 3 
try:
    xrange
except NameError:
    xrange = range


def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    #AK: Creates the window/display for the game, opening the game so everything is shown and updated 
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    #AK: This displays the title at the top of the screen "Flappy Bird"
    pygame.display.set_caption('Flappy Bird - Human playable')

    #AK: Number images to display the players score with digits from 0 to 9. 
    IMAGES['numbers'] = tuple(
        pygame.image.load(f'assets/sprites/{i}.png').convert_alpha()
        for i in range(10)
    )

    #AK: Display to indicate that the game is over when the player crashes/fails
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    #AK: Display for welcoming player to the game
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    #AK: Display for the ground
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    #AK: Depending on the device the player is using, this chooses a sound file to play 
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    #AK: This plays sound effects in the game 
    if ENABLE_SOUNDS:
        try:
            SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
            SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
            SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
            SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
            SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)
        except Exception:
            #AK: If the sounds don't load, they are simply disabled 
            SOUNDS.clear()

    #AK: A loop that restarts the game automatically once it has ended 
    while True:
        #AK: This selects a random background that can be either night or day 
        IMAGES['background'] = pygame.image.load('assets/sprites/background-day.png').convert()
        #AK: This selects a random bird display (between 3 positions, either red, blue or yellow) 
        IMAGES['player'] = (
            pygame.image.load('assets/sprites/redbird-upflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-midflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-downflap.png').convert_alpha(),
        )

        #AK: This selects random pipes (either red or green) to display (the top pipe is the bottom just rotated)
        IMAGES['pipe'] = (
            pygame.transform.rotate(pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(), 180),
            pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(),
        )

        #AK: This makes hitmasks that allows the game to detect when pixels collide with each other (ex. flappy bird hitting the pipe) 
        HITMASKS['pipe'] = (getHitmask(IMAGES['pipe'][0]), getHitmask(IMAGES['pipe'][1]))
        HITMASKS['player'] = (getHitmask(IMAGES['player'][0]), getHitmask(IMAGES['player'][1]), getHitmask(IMAGES['player'][2]))

        #AK: This displays the starting screen that welcomes the player before the game has begun 
        movementInfo = showWelcomeAnimation()
        #AK: This begins the main game
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    """
    Proper welcome screen loop. Waits for the player to press SPACE or UP to start.
    """
    #AK: Determines which position of the bird will be displayed (out of its three wing positions) 

    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    loopIter = 0

    #AK: Where the bird and message are initially located on the display screen by setting x and y locations of the bird 

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    
    #AK: Moves the background images sideways to create a display that has the ground passing/scrolling by smoothly

    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    #AK: How much the bird animation floats up and down on the welcome screen

    playerShmVals = {'val': 0, 'dir': 1}

    #AK: This is the main game loop that will run until the bird collides with any pipe, it waits for inputs and animated the bird & base
    while True:
        for event in pygame.event.get():  #AK: In this for loop, it gets all the events from the keyboard and system so like any key press 
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                #AK Starts the game and returns the movement information to begin the mainGame
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                    'playerIndex': playerIndex
                }
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

        #AK: Animated the birds wings periodically 
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30

        #AK: Moves the base for a scrolling effect 

        basex = -((-basex + 4) % baseShift)

        #AK: This is the vertical bobbing/shifting on the welcome screen before the game begins 
        playerShm(playerShmVals)

        #AK: This draws all the wlecome screen displays like the bird, base, the message, etc. 
        SCREEN.blit(IMAGES['background'], (0, 0))
        SCREEN.blit(IMAGES['player'][playerIndex], (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def mainGame(movementInfo):
    """
    Main gameplay loop where human controls the bird with SPACE/UP.
    """
    #AK: This begins the score at 0 and is the counter in the animation 
    score = loopIter = 0

    #AJ: This keeps track of whether the score multiplier is active (NEW FEATURE)
    multiplierActive = False
    #AJ: This counts how many pipes will still give bonus points (3 pipes per activation)
    multiplierPipesLeft = 0
    #AJ: This stores how much we multiply the score by (2x)
    scoreMultiplier = 2

    #AJ: Dark mode feature toggle (NEW FEATURE)
    darkMode = False
    #AJ: This will count how many frames of dark mode are left (FPS * seconds)
    darkModeTimer = 0

    #AK: This restores the animation and index in the welcome screen 
    playerIndexGen = movementInfo['playerIndexGen']
    playerIndex = movementInfo['playerIndex']
    
    #AK: This is the starting position (or coordinates almost) of the flappy bird, (x is a constant and y is from the welcome screen) 
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    #AK: This is the base x offset for scrolling visual 
    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    #AK: Creates two pipes for the beginning of the game 
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    upperPipes = [
        {'x': SCREENWIDTH, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + (SCREENWIDTH // 2), 'y': newPipe2[0]['y']},
    ]
    lowerPipes = [
        {'x': SCREENWIDTH, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + (SCREENWIDTH // 2), 'y': newPipe2[1]['y']},
    ]

    #AK The horzontal speed of the pipes, (becomes negative as they move leftwards) since the bird moves to the right as players progress
    pipeVelX = -4

    #AJ: This variable tells how much faster pipes become after each score (negative = faster left)
    speedIncrease = -0.2  #AJ: Small step so difficulty increases gradually, not all at once

    #AK: The players physics parameters (like velocity, acceleration and rotation) 
    playerVelY = -9  #AK: This is the initial velocity when the bird beginns flapping at "start"
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerRot = 45
    playerVelRot = 3
    playerRotThr = 20
    playerFlapAcc = -9
    playerFlapped = False

    #AK: This is the cache sprite dimensions to avoid any repeated calls 
    pipew = IMAGES['pipe'][0].get_width()
    playerw = IMAGES['player'][0].get_width()
    playerh = IMAGES['player'][0].get_height()

    #AK: This is the main loop of the flappy bird game. This runs all the way until a crash occurs (bird hits pipes, ) 
    while True:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            #AK: A human flap where every SPACE/UP press sets flap velocity
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                #AK PLays the flapping sound if possible
                if 'wing' in SOUNDS:
                    try:
                        SOUNDS['wing'].play()
                    except Exception:
                        pass
                #AK: This applies the actual flapping motion 
                playerVelY = playerFlapAcc
                playerFlapped = True

            #AJ: When the player presses "M", activate the score multiplier power-up
            if event.type == KEYDOWN and event.key == pygame.K_m:
                multiplierActive = True
                multiplierPipesLeft = 3  #AJ: Multiplier will last for the next 3 pipes passed
                print("Multiplier Activated!")  #AJ: Simple feedback in console for testing

            #AJ: When the player presses "D", turn on dark mode for 5 seconds
            if event.type == KEYDOWN and event.key == pygame.K_d:
                darkMode = True
                #AJ: Use FPS * 5 so dark mode lasts exactly 5 seconds in frames
                darkModeTimer = FPS * 5

        #AK: The animation of the player sprite and moves base for a "scrolling effect"
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)

        #AK: This visually rotates the bird as it falls 
        if playerRot > -90:
            playerRot -= playerVelRot

        #AK: Applies gravity to the bird, so when its not flapping it moves with a downwards velocity 
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY

        #AK: This resets the flap and sets the roatation of it upwards after each flap occurs 
        if playerFlapped:
            playerFlapped = False
            playerRot = 45

        #AK: This updates the vertical position, essentially preventing the bird and any display from going below the base 
        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        #ARLEEN's SECTION 
        
        #AJ: this moves all the pipes in the leftwards direction 
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        #AJ: this adds a new pair of pipes as the leftmost pipes reach the left edge of the display screen (creating the effect of the pipes continuing as the game progresses) 
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        #AJ: this removes the pipes that go off screen to the free memory 
        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        #AJ: this draws the visual background and pipes that the player sees 
        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        #AJ: this draws a base and the score so the base can overlap easily as game progresses
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        #AJ: If dark mode is active, draw a semi-transparent black layer over everything
        if darkMode:
            dark_overlay = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
            dark_overlay.fill((0, 0, 0))  #AJ: pure black
            dark_overlay.set_alpha(150)   #AJ: 150/255 = partly see-through so game is still visible
            SCREEN.blit(dark_overlay, (0, 0))

            #AJ: Decrease timer every frame; when it hits zero, dark mode ends
            darkModeTimer -= 1
            if darkModeTimer <= 0:
                darkMode = False

        #AJ: this determines the rotation of the sprite (prevents it from over-rotating as well) 
        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot

        #AJ: this draws the final rotated bird sprite 
        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()

        #AJ: this checks for crashes (if the bird has hit a pipe, or touched the ground) 
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex}, upperPipes, lowerPipes)
        if crashTest[0]:
            #AJ: this plays the dying noise when its available (if there's an error, sound is actually just ignored) 
            if 'hit' in SOUNDS:
                try:
                    SOUNDS['hit'].play()
                except Exception:
                    pass
            if not crashTest[1] and 'die' in SOUNDS:
                try:
                    SOUNDS['die'].play()
                except Exception:
                    pass

            #AJ: this returns the information when the user crashes by "showGameOverScreen", displaying a game over message 
            return {
                'y': playery,
                'groundCrash': crashTest[1],
                'basex': basex,
                'upperPipes': upperPipes,
                'lowerPipes': lowerPipes,
                'score': score,
                'playerVelY': playerVelY,
                'playerRot': playerRot
            }

        #AJ: this checks the score and updates it when the bird has succesfully passed through a set of pipes 
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            #AJ: The window for scores, when the pipes middle passes the birds middle, giving the player a new score of +1 every time this occurs 
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                #AJ: If multiplier is active, add extra points and decrease remaining pipes
                if multiplierActive:
                    score += scoreMultiplier  #AJ: adds 2 points instead of 1
                    multiplierPipesLeft -= 1  #AJ: one of the 3 bonus pipes has been used

                    #AJ: When all bonus pipes are used, turn off multiplier
                    if multiplierPipesLeft <= 0:
                        multiplierActive = False
                else:
                    score += 1  #AJ: normal scoring when no power-up active

                #AK: Plays point sound if its available 
                if 'point' in SOUNDS:
                    try:
                        SOUNDS['point'].play()
                    except Exception:
                        pass

                #AJ: Every time the score increases, make pipes move slightly faster
                pipeVelX += speedIncrease
                #AJ: Because pipeVelX is negative, adding a negative value makes it more negative -> faster to the left

        #this caps the frame-rate to the FPS value 
        FPSCLOCK.tick(FPS)


def showGameOverScreen(crashInfo):
    """
    Show falling bird and wait until the player presses SPACE/UP to restart.
    """
    #AJ: this reads the information for a crash, and sets up variables for the animation 
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7

    basex = crashInfo['basex']
    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                # restart only once bird has landed on base
                if playery + playerHeight >= BASEY - 1:
                    return

        #AJ: the flappy bird falling to the ground if it is not yet there already 
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        #AJ: this increases the downward velocity until a terminal velocity is reached (or a constant velocity/max velocity) 
        if playerVelY < 15:
            playerVelY += playerAccY

        #AJ: rotates when a crash occurs with a pipe 
        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot

        #AJ: redraws everything (entire scene including pipes, base, score, bird, etc) 
        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    #AJ: this reverses the direction when a max oscillation is acheieved 
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1
    #AJ: creates a bobbing effect by making bird shift slightly upwards & downwards 
    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def getRandomPipe():
    """returns a randomly generated pair of pipes (upper, lower)"""
    #AJ: this creates a random pipe gap through the vetical positioning of the pipes, that still allows the player to play (keeps an appropriate gap) 
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)  #
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower
    ]


def showScore(score):
    """displays score in center of screen"""

    #AJ: splits the score in to digits, creates a total width and each digits is displayed in the center at the top of the screen 
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0
    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2
    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collides with base or pipes."""
    #AJ: the bird sprite index and its dimensions that are used for checking if a collision has occured
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    #AJ: checks for a collision with the ground (different with pipes) 
    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]
    else:
        #AJ:  creates rects that do bounding-box rejections before any pixel-level checks 
        playerRect = pygame.Rect(player['x'], player['y'], player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            #AJ: this saves time thorugh a reject by rect collision 
            if not playerRect.colliderect(uPipeRect) and not playerRect.colliderect(lPipeRect):
                continue

            #AJ: this detects pixel-level collisions in the intersection triangle 
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                #AJ: Returns (if the collision happened, not on the ground)
                return [True, False]
                
    #AJ: for when a collision has not occured 
    return [False, False]

#In this final section, we used AI to help explain what exactly occured: 
# CITATION: OpenAI. (2025). Explanation of Flappy Bird pixel collision and hitmask functions in Python [AI-generated response]. ChatGPT (GPT-5.1).
#User Prompt Used:
#“If im trying to understand a flappy bird code, can you help explain so I can understand this (remaining code below)" 

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    #AJ: this essentially finds the overlap between rect1 (the birds rectangle) and rect2 (the pipe's rectangle) 
    rect = rect1.clip(rect2)

    #AJ: this is for when there is no overlap, then no collision has occured (no overlap=no collision)
    if rect.width == 0 or rect.height == 0:
        return False

    #AJ: this calculated where overlap begins and gets the  coordinates inside the hitmask arrays 
    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    #AJ: this is a double loop that checks each and every pixel in the area that is overlapped. 
    #AJ: If the bird and the pipe both have solid pixels at the same spot, then a collision has occurred.
    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    #AJ: this creates the hitmask
    #AJ: every pixel has an alpha value, this function essentially stores true if the pixel is visible and false if its invisible 
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

#AJ: this is where the game is finally able to run, launching the Flappy Bird game! 
if __name__ == '__main__':
    main()
