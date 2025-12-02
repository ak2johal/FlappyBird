# -------------------------------
#     CLEAN HUMAN FLAPPY BIRD
#   (No AI, No Q-Learning)
# -------------------------------

import pygame
import random
import sys
from itertools import cycle
from pygame.locals import *

# Initialize game
pygame.init()
FPS = 60
FPSCLOCK = pygame.time.Clock()

SCREENWIDTH  = 288
SCREENHEIGHT = 512
SCREEN       = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('Flappy Bird - Human Version')

# Game constants
PIPEGAPSIZE = 100
BASEY = SCREENHEIGHT * 0.79

# Load images
IMAGES = {}
IMAGES['numbers'] = [
    pygame.image.load(f'assets/sprites/{i}.png').convert_alpha()
    for i in range(10)
]
IMAGES['background'] = pygame.image.load('assets/sprites/background-day.png').convert()
IMAGES['player'] = [
    pygame.image.load('assets/sprites/redbird-upflap.png').convert_alpha(),
    pygame.image.load('assets/sprites/redbird-midflap.png').convert_alpha(),
    pygame.image.load('assets/sprites/redbird-downflap.png').convert_alpha()
]
IMAGES['pipe'] = [
    pygame.transform.flip(
        pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(), False, True),
    pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(),
]
IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()
IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()

# Load sounds
SOUNDS = {}
soundExt = '.wav'
SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)


# -----------------------------------
#     WELCOME SCREEN / MAIN MENU
# -----------------------------------
def showWelcomeAnimation():
    playerIndex = 0
    playerIndexGen = cycle([0,1,2,1])

    loopIter = 0
    playerx = int(SCREENWIDTH*0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height())/2)

    basex = 0
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    playerShmVals = {'val':0, 'dir':1}

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key==K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key==K_SPACE or event.key==K_UP):
                # Start game
                return {
                    'playery': playery + playerShmVals['val'],
                    'playerx': playerx,
                    'basex' : basex,
                    'playerIndex' : playerIndex,
                    'playerIndexGen' : playerIndexGen,
                }

        # Player flap animation
        if (loopIter+1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter+1) % 30

        # Wiggle
        playerShm(playerShmVals)

        # Draw background + elements
        SCREEN.blit(IMAGES['background'], (0,0))
        SCREEN.blit(IMAGES['player'][playerIndex], (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'],
                    ((SCREENWIDTH - IMAGES['message'].get_width())/2, SCREENHEIGHT*0.12))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        basex = -((-basex + 4) % baseShift)
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# -----------------------------------
#        MAIN GAME LOOP
# -----------------------------------
def mainGame(movementInfo):
    score = 0
    playerIndex = movementInfo['playerIndex']
    playerIndexGen = movementInfo['playerIndexGen']

    playerx = movementInfo['playerx']
    playery = movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # Generate first pipe pair
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH/2), 'y': newPipe2[0]['y']}
    ]

    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH/2), 'y': newPipe2[1]['y']}
    ]

    pipeVelX = -4

    # Player physics
    playerVelY    = -9
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY    = 1
    playerFlapAcc = -9
    playerFlapped = False

    loopIter = 0

    while True:
        # -------- INPUT --------
        for event in pygame.event.get():
            if event.type == QUIT or (event.type==KEYDOWN and event.key==K_ESCAPE):
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if playery > -2 * IMAGES['player'][0].get_height():
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    SOUNDS['wing'].play()

        # -------- COLLISION CHECK --------
        crashTest = checkCrash({'x':playerx, 'y':playery}, upperPipes, lowerPipes)
        if crashTest[0]:
            return

        # -------- SCORE --------
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMid = pipe['x'] + IMAGES['pipe'][0].get_width()/2
            if pipeMid <= playerMidPos < pipeMid + 4:
                score += 1
                SOUNDS['point'].play()

        # -------- ANIMATION --------
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30

        # -------- Physics --------
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        # Move pipes
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        # Spawn new pipes
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # Remove offscreen pipes
        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        
        SCREEN.blit(IMAGES['background'], (0,0))

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        basex = -((-basex + 4) % baseShift)

        SCREEN.blit(IMAGES['player'][playerIndex], (playerx, playery))
        showScore(score)

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def playerShm(playerShmVals):
    if abs(playerShmVals['val']) == 8:
        playerShmVals['dir'] *= -1
    if playerShmVals['dir'] == 1:
        playerShmVals['val'] += 1
    else:
        playerShmVals['val'] -= 1

def getRandomPipe():
    gapY = random.randrange(40, int(BASEY*0.6))
    gapY += int(BASEY*0.2)

    pipeX = SCREENWIDTH + 10

    return [
        {'x':pipeX, 'y':gapY - IMAGES['pipe'][0].get_height()},
        {'x':pipeX, 'y':gapY + PIPEGAPSIZE},
    ]

def checkCrash(player, upperPipes, lowerPipes):
    px, py = player['x'], player['y']

    # Ground
    if py + IMAGES['player'][0].get_height() >= BASEY - 1:
        SOUNDS['hit'].play()
        return [True, True]

    playerRect = pygame.Rect(px, py,
                    IMAGES['player'][0].get_width(),
                    IMAGES['player'][0].get_height())

    for uPipe, lPipe in zip(upperPipes, lowerPipes):
        uRect = pygame.Rect(uPipe['x'], uPipe['y'],
                            IMAGES['pipe'][0].get_width(),
                            IMAGES['pipe'][0].get_height())
        lRect = pygame.Rect(lPipe['x'], lPipe['y'],
                            IMAGES['pipe'][1].get_width(),
                            IMAGES['pipe'][1].get_height())

        if playerRect.colliderect(uRect) or playerRect.colliderect(lRect):
            SOUNDS['hit'].play()
            return [True, True]

    return [False, False]

def showScore(score):
    digits = list(str(score))
    width = sum(IMAGES['numbers'][int(d)].get_width() for d in digits)

    xOffset = (SCREENWIDTH - width)/2
    for d in digits:
        SCREEN.blit(IMAGES['numbers'][int(d)], (xOffset, SCREENHEIGHT*0.1))
        xOffset += IMAGES['numbers'][int(d)].get_width()
while True:
    movementInfo = showWelcomeAnimation()
    mainGame(movementInfo)
