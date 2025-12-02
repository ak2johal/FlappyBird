# AK: Importing necessary python modules required for the game.
import csv
import random
import sys
from itertools import cycle

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP, K_p, K_r  # Rule change 2 NKC: The Key "p" and "r" indicate pause and resume by player input.

import numpy as np

import datetime  # Rule change 1 by NKC to determine current hour of player.

from PIL import Image, ImageEnhance  # Rule change 1 by NKC to adjust background brightness.

# AK: Sets a seed for NumPy's pseudo-random number generator (to repeat numbers the same way each time).
np.random.seed(1)

# AK: Display settings for the game such as, screenwidth and screenheight
FPS = 60  # FIX: was 500, too fast; 60 is standard game FPS
SCREENWIDTH = 288
SCREENHEIGHT = 512
# AK: The distance between the lower and upper pipe
PIPEGAPSIZE = 100
# AK: Where the bottom/grass is located on the screen
BASEY = SCREENHEIGHT * 0.79

# AK: Dictionary for images, sound and hitmask variables
IMAGES, SOUNDS, HITMASKS = {}, {}, {}
paused = False  # Change 2 by NKC: Not paused

# AK: Variables for the games learning system
"""
learning
"""
statefile = "state"
# AK: Flappy birds learning rate
alpha = 1
# AK: Consideration of future rewards to be just as important as immediate rewards
gamma = 1
# AK: Reward for surviving
survivereward = 1
# AK: Punishment for dying
deadreward = -200
# AK: Reward for passing a set of pipes
passreward = 1
# AK: The birds memory of siutations and its performance
Qmatrix = {}
# AK: Keeps track of high score
maxscore = 0
# AK: Counts total number of games played
wholecount = 0
# AK: Interval after which the time of the game updates
checktime = 1
# AK: To define pixel value used for movement speed, size, or spacing
pix = 10
# AK: Flappy bird will only perform actions that it knows, it will never take random actions
epsilon = 0
# AK: The amount by which epsilon is reduced
eps_dec = 0.0001

# AK: Ensures xrange is compatible with Python 2 & Python 3
try:
    xrange
except NameError:
    xrange = range

# list of all possible players (tuple of 3 positions of flap)
# AK: List of all possible bird displays/designs (there are 3 different wing positions)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/redbird-upflap.png',
        'assets/sprites/redbird-midflap.png',
        'assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        # amount by which base can maximum shift to left
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        'assets/sprites/yellowbird-upflap.png',
        'assets/sprites/yellowbird-midflap.png',
        'assets/sprites/yellowbird-downflap.png',
    ),
)

# AK: List if all the possible backgrounds (day or night)
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

# AK: List of all the possible pipe designs (red or green)
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)


def main():
    global SCREEN, FPSCLOCK, paused_font  # Rule change 2 by NKC: Ensures the local variable is accesible within the function.
    pygame.init()  # Rule change 2 by NKC
    pygame.font.init()  # Rule change 2 by NKC
    paused_font = pygame.font.SysFont(None, 50)  # Rule change 2 by NKC
    FPSCLOCK = pygame.time.Clock()
    # AK: Creates the window/display for the game
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    # AK: Displays the title at the top of the screen
    pygame.display.set_caption('Flappy Bird')

    # AK: Number images to display the players score
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    # AK: Display to indicate that the game is over
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    # AK: Display for welcoming player to the game
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    # AK: Display for the ground
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # AK: Depending on the device the player is using, this chooses a sound file to play
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    # AK: Plays sound effects in the game
    SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)

    def background_brightness(factor):  # Rule change 1 by NKC
        background = Image.open('assets/sprites/background-day.png').convert("RGB")  # Rule change 1 by NKC
        background_enhancer = ImageEnhance.Brightness(background)  # Rule change 1 by NKC
        background_adjusted = background_enhancer.enhance(factor)  # Rule change 1 by NKC
        mode = background_adjusted.mode  # Rule change 1 by NKC: Convert PIL image to pygame surface format in order specify RGB
        size = background_adjusted.size  # Rule change 1 by NKC: Convert PIL image to pygame surface format with tuple of dimensions
        data = background_adjusted.tobytes()  # Rule change 1 by NKC: Convert PIL image to pygame surface format with string of pixels
        surface_background = pygame.image.fromstring(data, size, mode)  # Rule change 1 by NKC: Use data to convert from PIL image to pygame surface format
        return surface_background  # Rule change 1 by NKC: Final background in pygame surface format

    def background_time():  # Rule change 1 by NKC
        player_current_hour = datetime.datetime.now().hour  # Rule change 1 by NKC: Hours in military time
        if 6 <= player_current_hour < 17:  # Rule change 1 by NKC: 6:00 A.M. to 5:00 P.M.
            return background_brightness(1)  # Rule change 1 by NKC: factor of 1 = standard during daytime
        elif 17 <= player_current_hour < 18:  # Rule change 1 by NKC: 5:00 P.M. to 6:00 P.M.
            return background_brightness(0.5)  # Rule change 1 by NKC: factor less than 1 = darker durig sunset
        elif (18 <= player_current_hour <= 23) or (0 <= player_current_hour < 5):  # Rule change 1 by NKC: 6:00 P.M. to 11:00 P.M. or 12:00 A.M. to 5:00 A.M.
            return background_brightness(0.3)  # Rule change 1 by NKC: factor less than 1 = darker during ight
        else:  # Rule change 1 by NKC: if 5 <= player_current_hour < 6:
            # Rule change 1 by NKC: 5:00 A.M. to 6:00 A.M.
            return background_brightness(0.7)  # Rule change 1 by NKC: factor less than 1 = darker during sunrise

    def draw_background_inner():  # Rule change 2 by NKC: Function to reduce lines of code (inner version, unused outside main)
        if not paused:  # Rule change 2 by NKC
            SCREEN.blit(IMAGES['background'], (0, 0))  # Rule change 2 by NKC: Standard background
        else:  # Rule change 2 by NKC: If paused
            SCREEN.blit(IMAGES['dimmed'], (0, 0))  # Rule change 2 by NKC: Darker background to distinguish game paused to player.
            paused_label = paused_font.render("PAUSED", True, (255, 255, 255))  # Rule change 2 by NKC: High-contrast white label on darker background to inform player that the game is paused.
            SCREEN.blit(paused_label, (SCREENWIDTH // 2 - paused_label.get_width() // 2,
                                       SCREENHEIGHT // 2 - paused_label.get_height() // 2))  # Rule change 2 by NKC: Positions label in middle of screen.

    # AK: A loop that restarts the game once it has ended
    while True:
        global paused  # FIX: ensure we modify global paused, not create a local
        paused = False  # Rule change 2 by NKC: Game is not paused by player

        # AK: Selects a random background
        randBg = 0
        IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()
        IMAGES['dimmed'] = background_brightness(0.2)  # Rule change 2 by NKC: Background when game paused by player is adjusted to be darker.

        # AK: Selects a random bird display (between 3 positions)
        randPlayer = 0
        IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # AK: Selects random pipes to display (the top pipe is the bottom just rotated)
        pipeindex = 0
        IMAGES['pipe'] = (
            pygame.transform.rotate(
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # AK: Makes hitmasks that allows the game to detect when pixels collide with each other (ex. flappy bird hitting the pipe)
        HITMASKS['pipe'] = (
            getHitmask(IMAGES['pipe'][0]),
            getHitmask(IMAGES['pipe'][1]),
        )

        HITMASKS['player'] = (
            getHitmask(IMAGES['player'][0]),
            getHitmask(IMAGES['player'][1]),
            getHitmask(IMAGES['player'][2]),
        )
        # AK: Displays the starting screen that welcomes the player
        movementInfo = showWelcomeAnimation()
        # AK: Begins the main game
        crashInfo = mainGame(movementInfo)
        # showGameOverScreen(crashInfo)


def draw_background():  # Rule change 2 by NKC: Function to reduce lines of code
    if not paused:  # Rule change 2 by NKC
        SCREEN.blit(IMAGES['background'], (0, 0))  # Rule change 2 by NKC: Standard background
    else:  # Rule change 2 by NKC: If paused
        SCREEN.blit(IMAGES['dimmed'], (0, 0))  # Rule change 2 by NKC: Darker background to distinguish game paused to player.
        paused_label = paused_font.render("PAUSED", True, (255, 255, 255))  # Rule change 2 by NKC: High-contrast white label on darker background to inform player that the game is paused.
        SCREEN.blit(paused_label, (SCREENWIDTH // 2 - paused_label.get_width() // 2,
                                   SCREENHEIGHT // 2 - paused_label.get_height() // 2))  # Rule change 2 by NKC: Positions label in middle of screen.


def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    # index of player to blit on screen
    # AK: Which position the bird will be displayed (out of its three wing positions)
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    loopIter = 0

    # AK: Where the bird and message are initially located on the display screen
    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0

    # AK: Used to make the ground pass/scroll by smoothly
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # AK: How much the bird animation floats up and down on the welcome screen
    playerShmVals = {'val': 0, 'dir': 1}

    global paused  # Rule change 2 by NKC: Ensures the local variable is accesible within the function.

    # ---------- FIX: make welcome screen actually loop until user presses SPACE/UP ----------
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                # AK: Returns the birds position at the start of each game
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                    'playerIndex': playerIndex
                }

        # AK: Frequently updates the birds animation
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        # AK: Allows the bird to float upwards & downwards
        playerShm(playerShmVals)

        # AK: Draws all the sprites on the screen
        draw_background()  # Rule change 2 by NKC

        SCREEN.blit(IMAGES['player'][playerIndex],
                    (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        pygame.display.update()
        FPSCLOCK.tick(FPS)
    # ------------------------------------------------------------------------------------


# ARLEEN'S SECTION
def mainGame(movementInfo):
    global wholecount, maxscore, epsilon, paused  # Rule change 2 by NKC: Ensures the local variable is accesible within the function.
    epslion = 0.1

    loopIter = 0  # FIX: ensure loopIter exists independently from score
    score = 0

    playerIndexGen = movementInfo['playerIndexGen']
    playerIndex = movementInfo['playerIndex']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of upper pipes
    upperPipes = [
        {'x': SCREENWIDTH, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]

    # list of lowerpipe
    lowerPipes = [
        {'x': SCREENWIDTH, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    base_pipeVelX = -4  # Rule change 3 by NKC: Standard inital pipe velocity
    result_pipeVelX = base_pipeVelX - score // 10  # Rule change 3 by NKC: Current pipe velocity increases per ten points gained by player.

    # player velocity, max velocity, downward accleration, accleration on flap
    playerVelY = -9   # player's velocity along Y, default same as playerFlapped
    playerMaxVelY = 10   # max vel along Y, max descend speed
    playerMinVelY = -8   # min vel along Y, max ascend speed
    playerAccY = 1   # players downward accleration
    playerRot = 45   # player's rotation
    playerVelRot = 3   # angular speed
    playerRotThr = 20   # rotation threshold
    playerFlapAcc = -9   # players speed on flapping
    playerFlapped = False  # True when player flaps

    pipew = IMAGES['pipe'][0].get_width()
    playerw = IMAGES['player'][0].get_width()
    playerh = IMAGES['player'][0].get_height()

    count = 0
    pipepass = False
    dx = int(lowerPipes[0]['x'] + pipew - (playerx + playerw))
    dy = int(lowerPipes[0]['y'] - (playery + playerh))
    dx = dx / pix
    dy = dy / pix
    dist = (dx, dy)
    last = dist

    # FIX: ensure initial state exists in Qmatrix before we try to update Qmatrix[last]
    if last not in Qmatrix:
        Qmatrix[last] = [0, 0]

    while True:
        count += 1
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_p:  # Rule change 2 by NKC: If player presses down on the key "p" to indicate pause game
                paused = not paused  # Rule change 2 by NKC: Game is paused as pause = True (not False)
            if event.type == KEYDOWN and event.key == K_r:  # Rule change 2 by NKC: If player presses down on the key "r" to indicate reusme game
                paused = False  # Rule change 2 by NKC: Game is not paused
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                # FIX: use text mode with newline='' for csv in Python 3
                with open(statefile, 'w', newline='') as wf:
                    w = csv.writer(wf)
                    w.writerows(Qmatrix.items())
                with open("score.csv", 'w', newline='') as wf:
                    w = csv.writer(wf)
                    w.writerow((maxscore, wholecount))
                pygame.quit()
                sys.exit()

        playerMidPos = playerx
        # update last state
        for pipe in lowerPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width()
            if playerMidPos < pipeMidPos:
                break

        dx = int(pipe['x'] + pipew - (playerx + playerw))
        dy = int(pipe['y'] - (playery + playerh))
        dx = dx / pix
        dy = dy / pix
        dist = (dx, dy)
        if dist not in Qmatrix:
            Qmatrix[dist] = [0, 0]
        if np.random.uniform() < epsilon:
            action = np.random.randint(2)
        else:
            action = Qmatrix[dist].index(max(Qmatrix[dist]))
        epsilon = max(epsilon - eps_dec, 0)
        if action == 1:
            if playery > -2 * IMAGES['player'][0].get_height():
                playerVelY = playerFlapAcc
                playerFlapped = True

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)

        # rotate the player
        if playerRot > -90:
            playerRot -= playerVelRot

        # player's movement
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            playerRot = 45

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        if not paused:  # Rule change 2 by NKC: If the game is not paused:
            result_pipeVelX = max(-10, base_pipeVelX - score // 10)  # Rule change 3 by NKC: Verify that the current pipe horizontal velocity cannot exceed maximum horizontal velocity of bird.

        # move pipes to left
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += result_pipeVelX  # Rule change 3 by NKC
            lPipe['x'] += result_pipeVelX  # Rule change 3 by NKC

        # add new pipe when first pipe is about to touch left of screen
        if 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # draw sprites
        draw_background()  # Rule change 2 by NKC

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        # print score so player overlaps the score
        showScore(score)

        # Player rotation has a threshold
        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot

        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()

        # check for crash here
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex},
                               upperPipes, lowerPipes)
        if crashTest[0]:
            reward = deadreward
            wholecount += 1
        else:
            reward = survivereward
            # check for score
            playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
            for pipe in upperPipes:
                pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
                if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                    score += 1
                    if score > maxscore:
                        maxscore = score
                        # FIX: text mode for csv
                        with open(statefile, 'w', newline='') as wf:
                            w = csv.writer(wf)
                            w.writerows(Qmatrix.items())
                    pipepass = True
                    reward = passreward
                    # SOUNDS['point'].play()

        """
        update
        """
        playerMidPos = playerx
        # update last state
        for pipe in lowerPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width()
            if playerMidPos < pipeMidPos:
                break

        dx = int(pipe['x'] + pipew - (playerx + playerw))
        dy = int(pipe['y'] - (playery + playerh))
        dx = dx / pix
        dy = dy / pix
        dist = (dx, dy)
        if dist not in Qmatrix:
            Qmatrix[dist] = [0, 0]
        maxnewstate = max(Qmatrix[dist])
        Qmatrix[last][action] = (1 - alpha) * Qmatrix[last][action] + alpha * (reward + gamma * maxnewstate)
        last = dist

        if crashTest[0]:
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

        FPSCLOCK.tick(FPS)


# NAVTEJVIR'S SECTION
def showGameOverScreen(crashInfo):
    """crashes the player down and shows gameover image"""
    global paused  # Rule change 2 by NKC: Ensures the local variable is accesible within the function.

    score = crashInfo['score']  # NKC: From crashInfo dictionary, score value is assigned to display final score to player
    playerx = SCREENWIDTH * 0.2  # NKC: Bird position is determined to be 20% of screenwidth.
    playery = crashInfo['y']  # NKC: Current vertical coordinate of bird
    playerHeight = IMAGES['player'][0].get_height()  # NKC: Bird height
    playerVelY = crashInfo['playerVelY']  # NKC: Vertical velocity
    playerAccY = 2  # NKC: Graviational acceleration
    playerRot = crashInfo['playerRot']  # NKC: Rotation angle
    playerVelRot = 7  # NKC: Rotational velocity

    basex = crashInfo['basex']  # NKC: Current horizontal coordinate of ground

    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']  # NKC: Redraw pipes

    # play hit and die sounds
    SOUNDS['hit'].play()  # NKC
    if not crashInfo['groundCrash']:  # NKC
        SOUNDS['die'].play()  # NKC

    while True:  # NKC
        for event in pygame.event.get():  # NKC
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):  # NKC
                pygame.quit()  # NKC
                sys.exit()  # NKC
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):  # NKC
                if playery + playerHeight >= BASEY - 1:  # NKC
                    return  # NKC

        # player y shift
        if playery + playerHeight < BASEY - 1:  # NKC
            playery += min(playerVelY, BASEY - playery - playerHeight)  # NKC

        # player velocity change
        if playerVelY < 15:  # NKC
            playerVelY += playerAccY  # NKC

        # rotate only when it's a pipe crash
        if not crashInfo['groundCrash']:  # NKC
            if playerRot > -90:  # NKC
                playerRot -= playerVelRot  # NKC

        # NKC: Draw sprites (two dimensional image)
        draw_background()  # Rule change 2 by NKC

        for uPipe, lPipe in zip(upperPipes, lowerPipes):  # NKC
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))  # NKC
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))  # NKC
        showScore(score)  # NKC

        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)  # NKC
        SCREEN.blit(playerSurface, (playerx, playery))  # NKC

        FPSCLOCK.tick(FPS)  # NKC
        pygame.display.update()  # NKC


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:  # NKC
        playerShm['dir'] *= -1  # NKC

    if playerShm['dir'] == 1:  # NKC
        playerShm['val'] += 1  # NKC
    else:  # NKC
        playerShm['val'] -= 1  # NKC


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))  # NKC
    gapY += int(BASEY * 0.2)  # lower 0.2~0.8 pipe  # NKC
    pipeHeight = IMAGES['pipe'][0].get_height()  # NKC
    pipeX = SCREENWIDTH + 10  # NKC

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe above gap
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower pipe below gap
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]  # NKC
    totalWidth = 0  # NKC

    for digit in scoreDigits:  # NKC
        totalWidth += IMAGES['numbers'][digit].get_width()  # NKC

    Xoffset = (SCREENWIDTH - totalWidth) / 2  # NKC

    for digit in scoreDigits:  # NKC
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))  # NKC
        Xoffset += IMAGES['numbers'][digit].get_width()  # NKC


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collides with base or pipes."""
    pi = player['index']  # NKC
    player['w'] = IMAGES['player'][0].get_width()  # NKC
    player['h'] = IMAGES['player'][0].get_height()  # NKC

    # if player crashes into ground
    if player['y'] + player['h'] >= BASEY - 1:  # NKC
        return [True, True]  # NKC
    else:
        playerRect = pygame.Rect(player['x'], player['y'],
                                 player['w'], player['h'])  # NKC
        pipeW = IMAGES['pipe'][0].get_width()  # NKC
        pipeH = IMAGES['pipe'][0].get_height()  # NKC

        for uPipe, lPipe in zip(upperPipes, lowerPipes):  # NKC
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)  # NKC
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)  # NKC

            pHitMask = HITMASKS['player'][pi]  # NKC
            uHitmask = HITMASKS['pipe'][0]  # NKC
            lHitmask = HITMASKS['pipe'][1]  # NKC

            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)  # NKC
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)  # NKC

            if uCollide or lCollide:  # NKC
                return [True, False]  # NKC

    return [False, False]  # NKC


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)  # NKC

    if rect.width == 0 or rect.height == 0:  # NKC
        return False  # NKC

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y  # NKC
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y  # NKC

    for x in xrange(rect.width):  # NKC
        for y in xrange(rect.height):  # NKC
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:  # NKC
                return True  # NKC
    return False  # NKC


def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in xrange(image.get_width()):  # NKC
        mask.append([])
        for y in xrange(image.get_height()):  # NKC
            mask[x].append(bool(image.get_at((x, y))[3]))  # NKC
    return mask


if __name__ == '__main__':  # NKC: When program is run directly/scripted (not imported) the following is executed:
    main()  # NKC: Main game loop

