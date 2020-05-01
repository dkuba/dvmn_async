import time
import curses
import asyncio
import random
from itertools import cycle

TIC_TIMEOUT = 0.1
STAR_NUM = 150

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

MIN_ROW = 0
MIN_COLUMN = 0
STEP_SIZE = 10


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
    rows_direction = columns_direction = 0
    pressed_key_code = canvas.getch()

    if pressed_key_code == UP_KEY_CODE:
        rows_direction = -STEP_SIZE

    if pressed_key_code == DOWN_KEY_CODE:
        rows_direction = STEP_SIZE

    if pressed_key_code == RIGHT_KEY_CODE:
        columns_direction = STEP_SIZE

    if pressed_key_code == LEFT_KEY_CODE:
        columns_direction = -STEP_SIZE

    return rows_direction, columns_direction


async def animate_spaceship(canvas, row, column):
    current_row = row
    current_column = column
    max_row, max_column = canvas.getmaxyx()

    with open("rocket_frame1.txt", "r") as frame_file:
        frame_content1 = frame_file.read()
    with open("rocket_frame2.txt", "r") as frame_file:
        frame_content2 = frame_file.read()

    for frame in cycle([frame_content1, frame_content1, frame_content2, frame_content2]):
        columns_direction, rows_direction = get_rows_columns_directions(canvas)
        frame_rows, frame_col = get_frame_size(frame_content1)

        current_column += columns_direction
        if current_column < 0:
            current_column = 0
        elif current_column > max_column - frame_col:
            current_column = max_column - frame_col

        current_row += rows_direction
        if current_row < 0:
            current_row = 0
        elif current_row > max_row - frame_rows:
            current_row = max_row - frame_rows

        draw_frame(canvas, current_row, current_column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, current_row, current_column, frame, negative=True)


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
        for n in range(random.randint(0, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for n in range(random.randint(0, 5)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for n in range(random.randint(0, 3)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for n in range(random.randint(0, 3)):
            await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(0)
    window = curses.initscr()
    window.nodelay(True)
    row_max, column_max = window.getmaxyx()
    coroutines = [animate_spaceship(canvas, row_max/2, column_max/2)]
    for n in range(STAR_NUM):
        row = random.randint(0, row_max-1)
        column = random.randint(0, column_max-1)
        symbol = random.choice('+*.:')
        coroutines.append(blink(canvas, row, column, symbol))

    while True:
        for coroutine in coroutines:
            coroutine.send(None)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':

    curses.update_lines_cols()
    curses.wrapper(draw)