
import random
import sys
from itertools import cycle

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP

 
FPS = 60
SCREENWIDTH = 288
SCREENHEIGHT = 512

PIPEGAPSIZE = 100

BASEY = int(SCREENHEIGHT * 0.79)


IMAGES, SOUNDS, HITMASKS = {}, {}, {}
 
ENABLE_SOUNDS = True

try:
    xrange
except NameError:
    xrange = range


def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
   
    pygame.display.set_caption('Flappy Bird - Human playable')

    
    IMAGES['numbers'] = tuple(
        pygame.image.load(f'assets/sprites/{i}.png').convert_alpha()
        for i in range(10)
    )

    
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

     
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

     
    if ENABLE_SOUNDS:
        try:
            SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
            SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
            SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
            SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
            SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)
        except Exception:
            
            SOUNDS.clear()

     
    while True:
        IMAGES['background'] = pygame.image.load('assets/sprites/background-day.png').convert()
        IMAGES['player'] = (
            pygame.image.load('assets/sprites/redbird-upflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-midflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-downflap.png').convert_alpha(),
        )

        IMAGES['pipe'] = (
            pygame.transform.rotate(pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(), 180),
            pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(),
        )

        HITMASKS['pipe'] = (getHitmask(IMAGES['pipe'][0]), getHitmask(IMAGES['pipe'][1]))
        HITMASKS['player'] = (getHitmask(IMAGES['player'][0]), getHitmask(IMAGES['player'][1]), getHitmask(IMAGES['player'][2]))

        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    """
    Proper welcome screen loop. Waits for the player to press SPACE or UP to start.
    """
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    loopIter = 0
 
    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    playerShmVals = {'val': 0, 'dir': 1}

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                    'playerIndex': playerIndex
                }
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30

        basex = -((-basex + 4) % baseShift)

        playerShm(playerShmVals)

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
    score = loopIter = 0

    #AJ: RULE CHANGE: okay, so this is a nEW variable that will keep track if multiplier power-up is active
    multiplier_active = False  #AJ: this is important because it controls whether score should be doubled

    #AJ CHANGE: this new variable how many pipes left to apply multiplier boost
    multiplier_pipes_left = 0  #AJ CHANGE:  this is important because it limits how long the power lasts

    #AJ CHANGE: this new variable stores the multiplier value (e.g., 2x score)
    score_multiplier_value = 2  #AJ CHANGE: this is important because it defines how the score changes on the game

    #AJ CHANGE: this is a new variable that tracks whether dark mode is currently active, but right now it is set to false 
    darkmode_active = False  #AJ CHANGE: this is important because dark mode changes screen visuals

    #AJ CHANGE: this variable will keep track of number of frames left for dark mode
    darkmode_timer_frames = 0  #AJ CHANGE: this is important because it automatically ends dark mode

    playerIndexGen = movementInfo['playerIndexGen']
    playerIndex = movementInfo['playerIndex']
    
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

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

    pipeVelX = -4

    #AK CHANGE: this is a new variable that will make the pipes get faster as score increases
    pipe_speed_increase = -0.2  #AK CHANGE: this is important because it adds some sort of difficulty (harder game as score increases)

    playerVelY = -9  
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerRot = 45
    playerVelRot = 3
    playerRotThr = 20
    playerFlapAcc = -9
    playerFlapped = False

    pipew = IMAGES['pipe'][0].get_width()
    playerw = IMAGES['player'][0].get_width()
    playerh = IMAGES['player'][0].get_height()

    while True:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if 'wing' in SOUNDS:
                    try:
                        SOUNDS['wing'].play()
                    except Exception:
                        pass
                playerVelY = playerFlapAcc
                playerFlapped = True

            if event.type == KEYDOWN and event.key == pygame.K_m:
                multiplier_active = True  #AK CHANGE: this changes the multiplier variable to True and so it will start the multiplier
                multiplier_pipes_left = 3  #AK CHANGE: However, this will only lasts for three pipes
                print("Multiplier Activated!")  #AK CHANGE: this will be used for using feedback 

            #AK CHANGE: so by pressing the capital D, it will activate the dark mode for 5 seconds
            if event.type == KEYDOWN and event.key == pygame.K_d:
                darkmode_active = True  #AK CHANGE: this will turns dark mode on
                darkmode_timer_frames = FPS * 5  #AK CHANGE: the dark mode will only last for 5 seconds


        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)

        if playerRot > -90:
            playerRot -= playerVelRot

        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY

        if playerFlapped:
            playerFlapped = False
            playerRot = 45

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        #AJ CHANGE: this will only apply if the dark mode overlay if active
        if darkmode_active:# AJ CHANGE: if it is activated, then the background of the screen will be set to a darker colour
            dark_overlay = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
            dark_overlay.fill((0, 0, 0))
            dark_overlay.set_alpha(150)
            SCREEN.blit(dark_overlay, (0, 0))

            darkmode_timer_frames -= 1  #AJ CHANGE: this will begin the timer and countdown so that 5 seconds are accounted for 

            if darkmode_timer_frames <= 0:
                darkmode_active = False  #AJ CHANGE: this will disable (so dark mode is off) when timer ends

        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot

        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()
 
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex}, upperPipes, lowerPipes)
        if crashTest[0]:
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

        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2

            if pipeMidPos <= playerMidPos < pipeMidPos + 4:

                #AK CHANGE: this will only apply multiplier if active
                if multiplier_active:
                    score += score_multiplier_value  #AK CHANGE: this will increase the score by 2x
                    multiplier_pipes_left -= 1  #AK CHANGE: this will reduce the remaining pipes where the mulitpler is added 

                    if multiplier_pipes_left <= 0:
                        multiplier_active = False  #AK CHANGE: this will turn the multiplier off 
                else:
                    score += 1  # AK CHANGE: this is just the normal scoring

                if 'point' in SOUNDS: #AK CHANGE: once a point is collected, a sound will play 
                    try:
                        SOUNDS['point'].play()
                    except Exception:
                        pass

                #AJ CHANGE: this will change the speed of the pipes every time score increases
                pipeVelX += pipe_speed_increase  #AJ CHANGE: this will increase the difficulty of the game

        FPSCLOCK.tick(FPS)

def showGameOverScreen(crashInfo):
    """
    Show falling bird and wait until the player presses SPACE/UP to restart.
    """
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

        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        if playerVelY < 15:
            playerVelY += playerAccY

        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot

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
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1
    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def getRandomPipe():
    """returns a randomly generated pair of pipes (upper, lower)"""
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)  
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower
    ]


def showScore(score):
    """displays score in center of screen"""
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
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]
    else: 
        playerRect = pygame.Rect(player['x'], player['y'], player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            if not playerRect.colliderect(uPipeRect) and not playerRect.colliderect(lPipeRect):
                continue

            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]
                
    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y
 
    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

if __name__ == '__main__':
    main()


