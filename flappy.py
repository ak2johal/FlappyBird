"""
Human-playable Flappy Bird (no AI)

Requirements:
 - pygame
 - assets folder with sprites/audio in the same layout used previously:
   assets/sprites/*.png and assets/audio/*.ogg or .wav
"""

import random
import sys
from itertools import cycle

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP

# --- Config / constants -----------------------------------------------------
FPS = 60
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 100
BASEY = int(SCREENHEIGHT * 0.79)

IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# Optional: toggle sounds (if your system/mixer can't play)
ENABLE_SOUNDS = True

try:
    xrange
except NameError:
    xrange = range

# -----------------------------------------------------------------------------
def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption('Flappy Bird - Human playable')

    # load images used for score display
    IMAGES['numbers'] = tuple(
        pygame.image.load(f'assets/sprites/{i}.png').convert_alpha()
        for i in range(10)
    )

    # load UI sprites
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # audio ext
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    # load sounds defensively
    if ENABLE_SOUNDS:
        try:
            SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
            SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
            SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
            SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
            SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)
        except Exception:
            # if sounds can't be loaded, disable them
            SOUNDS.clear()

    # main loop: pick assets and run rounds
    while True:
        # background
        IMAGES['background'] = pygame.image.load('assets/sprites/background-day.png').convert()

        # player sprite set (3 frames)
        IMAGES['player'] = (
            pygame.image.load('assets/sprites/redbird-upflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-midflap.png').convert_alpha(),
            pygame.image.load('assets/sprites/redbird-downflap.png').convert_alpha(),
        )

        # pipes (upper rotated + lower)
        IMAGES['pipe'] = (
            pygame.transform.rotate(pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(), 180),
            pygame.image.load('assets/sprites/pipe-green.png').convert_alpha(),
        )

        # hitmasks (for pixel collision)
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
                # start game, return movement info
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                    'playerIndex': playerIndex
                }
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

        # animation counters
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30

        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # draw everything
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
    playerIndexGen = movementInfo['playerIndexGen']
    playerIndex = movementInfo['playerIndex']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # create two initial pipes
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

    # player physics
    playerVelY = -9  # initial velocity on start
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerRot = 45
    playerVelRot = 3
    playerRotThr = 20
    playerFlapAcc = -9
    playerFlapped = False

    # cache widths / heights
    pipew = IMAGES['pipe'][0].get_width()
    playerw = IMAGES['player'][0].get_width()
    playerh = IMAGES['player'][0].get_height()

    while True:
        # --- handle events (now includes human flap) ---
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            # human flap - every SPACE/UP press sets flap velocity
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                # play flap sound if available
                if 'wing' in SOUNDS:
                    try:
                        SOUNDS['wing'].play()
                    except Exception:
                        pass
                # apply flap
                playerVelY = playerFlapAcc
                playerFlapped = True

        # animate sprite index and base movement
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)

        # rotate the player (for visual effect)
        if playerRot > -90:
            playerRot -= playerVelRot

        # apply gravity
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY

        # reset flap state (flap is instantaneous velocity change)
        if playerFlapped:
            playerFlapped = False
            playerRot = 45

        # update player position - prevent going below the base
        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        # move pipes left
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        # add new pipe when the first is near left
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # remove off-screen pipes
        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # draw everything (render)
        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        # determine visible rotation for player sprite
        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot

        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()

        # check for crash
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex}, upperPipes, lowerPipes)
        if crashTest[0]:
            # play sounds
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

        # check for score (bird passes a pipe)
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                if 'point' in SOUNDS:
                    try:
                        SOUNDS['point'].play()
                    except Exception:
                        pass

        # cap FPS
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

        # player falls to the ground if not already
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        if playerVelY < 15:
            playerVelY += playerAccY

        # rotate when it's a pipe crash (visual)
        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot

        # draw everything
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
    gapY += int(BASEY * 0.2)  # lower 0.2~0.8 pipe
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

    # crash with ground
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

            # fast reject by rect collision - saves time
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
