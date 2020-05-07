import sys
import time
import curses
import asyncio
import random
from itertools import cycle
from physics import *
import os
from obstacles import *

TIC_TIMEOUT = 0.1
STAR_NUM = 150

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 259
RIGHT_KEY_CODE = 258
UP_KEY_CODE = 260
DOWN_KEY_CODE = 261
ESC_KEY_CODE = 27

MIN_ROW = 0
MIN_COLUMN = 0
STEP_SIZE = 1

FRAME_EXT = '.txt'

coroutines = []

spaceship_frame = ''

obstacles = []

loop = asyncio.get_event_loop()

async def sleep(tics=1):
    for tic in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas):
    global coroutines
    rows_number, columns_number = canvas.getmaxyx()

    frame_names = ['duck', 'lamp', 'hubble', 'trash_large', 'trash_small', 'trash_xl']

    while True:
        frame_path = os.path.join('frames', random.choice(frame_names) + FRAME_EXT)
        with open(frame_path, "r") as garbage_file:
            frame = garbage_file.read()
        trash_column = random.randint(0, columns_number)
        coroutines.append(show_obstacles(canvas, obstacles))
        coroutine = fly_garbage(canvas, trash_column, frame)

        coroutines.append(coroutine)

        await sleep(10)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)
    row_size, column_size = get_frame_size(garbage_frame)
    row = 0

    obstacles.append(Obstacle(row, column, row_size, column_size, garbage_frame))

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed



def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()


    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def get_rows_columns_directions(canvas):
    rows_direction = columns_direction = fire_shot = 0
    pressed_key_code = canvas.getch()

    if pressed_key_code == UP_KEY_CODE:
        rows_direction = -STEP_SIZE

    if pressed_key_code == DOWN_KEY_CODE:
        rows_direction = STEP_SIZE

    if pressed_key_code == RIGHT_KEY_CODE:
        columns_direction = STEP_SIZE

    if pressed_key_code == LEFT_KEY_CODE:
        columns_direction = -STEP_SIZE

    if pressed_key_code == SPACE_KEY_CODE:
        fire_shot = 1

    if pressed_key_code == ESC_KEY_CODE:
        sys.exit()

    return rows_direction, columns_direction, fire_shot


async def animate_spaceship():
    global spaceship_frame
    with open("frames/rocket_frame1.txt", "r") as frame_file:
        frame_content1 = frame_file.read()
    with open("frames/rocket_frame2.txt", "r") as frame_file:
        frame_content2 = frame_file.read()

    for frame in cycle([frame_content1, frame_content1, frame_content2, frame_content2]):
        spaceship_frame = frame
        await sleep(1)


async def run_spaceship(canvas, row, column):
    global spaceship_frame
    global coroutines
    current_frame = ''
    row_speed = column_speed = 0
    max_row, max_column = canvas.getmaxyx()

    while True:
        columns_direction, rows_direction, fire_shot = get_rows_columns_directions(canvas)
        if fire_shot:
            coroutines.append(fire(canvas, row, column+2, rows_speed=-1))
        frame_rows, frame_col = get_frame_size(spaceship_frame)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        row += row_speed
        column += column_speed

        if column < 0:
            column = 0
        elif column > max_column - frame_col:
            column = max_column - frame_col

        if row < 0:
            row = 0
        elif row > max_row - frame_rows:
            row = max_row - frame_rows

        current_frame = spaceship_frame

        draw_frame(canvas, row, column, current_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, current_frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(5)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(3)

        canvas.addstr(row, column, symbol)
        await sleep(3)


def draw(canvas):
    curses.curs_set(0)
    window = curses.initscr()
    window.nodelay(True)
    row_max, column_max = window.getmaxyx()

    global coroutines
    coroutines = [animate_spaceship(), run_spaceship(canvas, row_max / 2, column_max / 2),
                  fill_orbit_with_garbage(canvas)]

    for n in range(STAR_NUM):
        row = random.randint(0, row_max-1)
        column = random.randint(0, column_max-1)
        symbol = random.choice('+*.:')
        coroutines.append(blink(canvas, row, column, symbol))

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                index = coroutines.index(coroutine)
                coroutines.pop(index)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':

    curses.update_lines_cols()
    curses.wrapper(draw)