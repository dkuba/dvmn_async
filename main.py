import sys
import time
import curses
import asyncio
import random
from itertools import cycle
from physics import *
import os
from obstacles import *
from explosion import *
from game_scenario import *

TIC_TIMEOUT = 0.1
STAR_NUM = 150

START_YEAR = 1957
END_YEAR = 2020



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
obstacles_in_last_collisions = []

current_year = 1957


async def sleep(tics=1):
    for tic in range(tics):
        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas):
    global coroutines
    global current_year
    rows_number, columns_number = canvas.getmaxyx()

    frame_names = ['duck', 'lamp', 'hubble', 'trash_large', 'trash_small', 'trash_xl']

    while True:
        if not get_garbage_delay_tics(current_year):
            await sleep(10)
        else:
            await sleep(get_garbage_delay_tics(current_year))
            frame_path = os.path.join('frames', random.choice(frame_names) + FRAME_EXT)
            with open(frame_path, "r") as garbage_file:
                frame = garbage_file.read()
            trash_column = random.randint(0, columns_number)
            coroutine = fly_garbage(canvas, trash_column, frame)

            coroutines.append(coroutine)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    max_rows_number, max_columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, max_columns_number - 1)
    row_size, column_size = get_frame_size(garbage_frame)
    row = 0

    obstacles.append(Obstacle(row, column, row_size, column_size-1))
    current_obstacle = obstacles[-1]

    while row < max_rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if current_obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.pop(obstacles_in_last_collisions.index(current_obstacle))
            obstacles.pop(obstacles.index(current_obstacle))
            coroutines.append(explode(canvas, row + row_size/2, column + column_size/2))
            return
        row += speed
        current_obstacle.row = row

    obstacles.pop(obstacles.index(current_obstacle))


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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                coroutines.append(show_gameover(canvas))
                row_size, column_size = get_frame_size(current_frame)
                coroutines.append(explode(canvas, row + row_size / 2, column + column_size / 2))
                return


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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return
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


async def show_gameover(canvas):
    text = """
   _____                         ____                 
  / ____|                       / __ \                
 | |  __  __ _ _ __ ___   ___  | |  | |_   _____ _ __ 
 | | |_ |/ _` | '_ ` _ \ / _ \ | |  | \ \ / / _ \ '__|
 | |__| | (_| | | | | | |  __/ | |__| |\ V /  __/ |   
  \_____|\__,_|_| |_| |_|\___|  \____/  \_/ \___|_| 
    """

    max_rows_number, max_columns_number = canvas.getmaxyx()
    row_size, column_size = get_frame_size(text)
    row = (max_rows_number - row_size) / 2
    column = (max_columns_number - column_size) / 2
    while True:
        draw_frame(canvas, row, column, text)
        await asyncio.sleep(0)
        get_rows_columns_directions(canvas)


async def show_legend(canvas):
    global current_year
    max_rows_number, _ = canvas.getmaxyx()
    text = '{} {}'.format(current_year, PHRASES[1957])
    while True:
        if current_year in PHRASES:
            text = '{} {}'.format(current_year, PHRASES[current_year])
        draw_frame(canvas, max_rows_number-1, 1, text)
        await sleep(15)
        current_year += 1


def draw(canvas):
    global current_year
    global coroutines

    curses.curs_set(0)
    window = curses.initscr()
    window.nodelay(True)
    row_max, column_max = window.getmaxyx()

    coroutines = [animate_spaceship(), show_legend(canvas), run_spaceship(canvas, row_max / 2, column_max / 2),
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