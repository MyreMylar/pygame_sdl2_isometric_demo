#!/usr/bin/env python3
import os
import sys
import math
from collections import deque

import pygame_sdl2
from pygame_sdl2 import Surface
from pygame_sdl2.time import Clock
from pygame_sdl2.render import Renderer, Sprite, OrderSortableSprite, SortableContainer, TextureNode
from pygame_sdl2.font import Font
from pygame_sdl2.locals import *

import pygame_sdl2.image as image_module
import pygame_sdl2.mouse as mouse_module

from pytmx import TiledMap


def pygame_sdl2_image_loader(filename, colorkey, **kwargs):
    loaded_image = image_module.load(resource_path(filename))
    atlas_texture_node = renderer.load_texture(loaded_image)

    def extract_image(rect, flags):
        new_texture_node = TextureNode(atlas_texture_node, rect)
        return new_texture_node

    return extract_image


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Player:
    def __init__(self, start_position):
        self.world_position = [start_position[0], start_position[1]]
        self.move_target_pos = [start_position[0], start_position[1]]
        rendering_order = self.world_position[1]
        player_image = image_module.load(resource_path(os.path.join("data", "player.png")))
        self.sprite = OrderSortableSprite(renderer.load_texture(player_image), rendering_order)
        self.feet_offset = [32, 64]  # the feet of our sprite are 32 pixels right and 64 down from the top left
        self.sprite.pos = [self.world_position[0] - self.feet_offset[0],
                           self.world_position[1] - self.feet_offset[1]]

        self.move_direction_vector = [1.0, 0.0]
        self.walk_speed = 100.0
        self.grid_pos = world_pos_to_grid_pos(self.world_position)
        self.old_world_pos = [self.world_position[0], self.world_position[1]]

    def update(self, dt, sorted_sprite_group):
        if self.world_position != self.move_target_pos:
            diffs = [0.0, 0.0]
            diffs[0] = self.move_target_pos[0] - self.world_position[0]
            diffs[1] = self.move_target_pos[1] - self.world_position[1]
            length = math.sqrt(diffs[0]**2 + diffs[1]**2)
            if length > 0.0:
                self.move_direction_vector[0] = diffs[0] / length
                self.move_direction_vector[1] = diffs[1] / length
            if length < 1.0:
                self.world_position = self.move_target_pos

            self.world_position[0] += self.move_direction_vector[0] * self.walk_speed * dt
            self.world_position[1] += self.move_direction_vector[1] * self.walk_speed * dt
            self.sprite.pos = [self.world_position[0] - self.feet_offset[0],
                               self.world_position[1] - self.feet_offset[1]]

            self.update_layer(sorted_sprite_group)

    def update_layer(self, sorted_sprite_group):
        sorted_sprite_group.remove_list([self.sprite])
        self.sprite.sort_value = self.world_position[1]
        sorted_sprite_group.insert_sort_sprite(self.sprite)

    def set_move_target_pos(self, target):
        self.move_target_pos = target


class Tile:
    def __init__(self, grid_pos, world_position, texture_node, sort_value):
        self.pos = GamePosition(world_position)
        self.grid_pos = grid_pos

        self.sprite = OrderSortableSprite(texture_node, sort_value)
        self.normal_sprite = self.sprite
        self.sprite.pos = self.pos.screen_pos

        self.outline_sprite = self.sprite
        self.outline_sprite.pos = self.pos.screen_pos

        self.render_order_sort_value = -1

    def __lt__(self, other):
        return self.render_order_sort_value < other.render_order_sort_value

    def __str__(self):
        return "Tile - pos: " + str(self.pos.world_pos)

    def __repr__(self):
        return "Tile - pos: " + str(self.pos.world_pos)

    def select(self):
        self.sprite = self.outline_sprite
        print("selected tile, grid_pos:" + str(self.grid_pos))

    def deselect(self):
        self.sprite = self.normal_sprite


class GamePosition:
    def __init__(self, world_position):
        self.world_pos = world_position  # used for collision
        self.screen_pos = self.world_pos  # used for rendering

    def set_world_position(self, new_position):
        self.world_pos = new_position
        self.update_screen_pos()

    def update_screen_pos(self):
        self.screen_pos = self.world_pos


def screen_pos_to_world_pos(screen_position, current_view_offset):
    return [screen_position[0] - current_view_offset[0], screen_position[1] - current_view_offset[1]]


def world_pos_to_grid_pos(in_world_pos):
    tile_half_width = tmx_data.tilewidth/2
    tile_half_height = tmx_data.tileheight/2
    tile_x = -int((((-in_world_pos[1]+48) / tile_half_height) + (in_world_pos[0] / tile_half_width)) / 2) + 1
    tile_y = -int((((-in_world_pos[1]+48) / tile_half_height) - (in_world_pos[0] / tile_half_width)) / 2)

    return [tile_x, tile_y]


pygame_sdl2.init()
os.environ['SDL_VIDEO_CENTERED'] = '1'

screen_size = [800, 600]
icon = image_module.load(resource_path(os.path.join("data", "window_icon.png")))
# noinspection PyArgumentList
icon.set_colorkey(Color(255, 0, 255, 255))
pygame_sdl2.display.set_icon(icon)
screen = pygame_sdl2.display.set_mode(screen_size)  # FULLSCREEN
pygame_sdl2.display.set_caption("Isometric Rendering Test - SDL 2")
renderer = Renderer(None, vsync=False)  # second parameter is vsync
renderer.render_present()

view_clip_rect = Rect((0, 0), screen_size)
view_clip_rect_dimensions = [view_clip_rect.width, view_clip_rect.height]

font = Font(resource_path(os.path.join("data", "AGENCYR.TTF")), 32)
fonts = [font]

background = Surface(screen_size)
# noinspection PyArgumentList
background.fill(Color(0, 0, 0, 255))
background.convert(screen)
background_texture = renderer.load_texture(background)
background_sprite = Sprite(background_texture)

sorted_sprite_list = SortableContainer((0, 0))

view_offset = [332.0, -1100.0]
tmx_data = TiledMap(resource_path(os.path.join("data", "test_map.tmx")), image_loader=pygame_sdl2_image_loader)
tile_width = tmx_data.tilewidth
tile_height = tmx_data.tileheight
tile_dimensions = [tile_width, tile_height]

tile_map = []
for y in range(0, tmx_data.height):
    tile_col = []
    for x in range(0, tmx_data.width):
        layer_index = 0
        tile_layer = []
        for layer in tmx_data.visible_layers:
            y_offset = layer.offsety
            image = tmx_data.get_tile_image(y, x, layer_index)
            new_tile = None
            if image is not None:
                position = [(y * tile_width/2) - (x * tile_width/2), (x*tile_height/2) + (y*tile_height/2) + y_offset]
                if layer_index == 0 or layer_index == 1:  # for ground tiles use highest point of tile,
                    tile_base_position = position[1]+32      # we always want to be on top of these
                    render_order_sort_value = tile_base_position
                else:  # for objects tiles try using the centre point of diamond
                    tile_centre_position = position[1]+48-y_offset+((layer_index-1)*0.01)
                    render_order_sort_value = tile_centre_position
                new_tile = Tile([x, y], position, image, render_order_sort_value)
            layer_index += 1
            tile_layer.append(new_tile)
        tile_col.append(tile_layer)
    tile_map.append(tile_col)

number_visible_layers = 0
for layer in tmx_data.visible_layers:
    number_visible_layers += 1

sorted_sprite_list.pos = view_offset

frame_rates = deque([])
clock = Clock()
running = True

init_view = True
scroll_down = False
scroll_up = False
scroll_left = False
scroll_right = False

selected_tile = None
tile_selected = False

current_top_left_grid_pos = [0, 0]

player = Player((-96.0, 1349.0))
while running:
    frame_time = clock.tick()
    time_delta = frame_time / 1000.0
    tile_selected = False
    for event in pygame_sdl2.event.get():
        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if event.key == K_DOWN:
                scroll_down = True
            if event.key == K_UP:
                scroll_up = True
            if event.key == K_LEFT:
                scroll_left = True
            if event.key == K_RIGHT:
                scroll_right = True
        if event.type == KEYUP:
            if event.key == K_DOWN:
                scroll_down = False
            if event.key == K_UP:
                scroll_up = False
            if event.key == K_LEFT:
                scroll_left = False
            if event.key == K_RIGHT:
                scroll_right = False
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                screen_pos = mouse_module.get_pos()
                world_pos = screen_pos_to_world_pos(screen_pos, view_offset)
                player.set_move_target_pos(world_pos)
            if event.button == 3:
                screen_pos = mouse_module.get_pos()
                top_left_world_pos = screen_pos_to_world_pos(screen_pos, view_offset)
                print("click world pos:" + str(top_left_world_pos))

    player.update(time_delta, sorted_sprite_list)

    if scroll_down:
        view_offset[1] -= 300.0 * time_delta
    if scroll_up:
        view_offset[1] += 300.0 * time_delta
    if scroll_left:
        view_offset[0] += 300.0 * time_delta
    if scroll_right:
        view_offset[0] -= 300.0 * time_delta

    if scroll_down or scroll_up or scroll_left or scroll_right or tile_selected or init_view:
        init_view = False

        top_left_world_pos = screen_pos_to_world_pos(view_clip_rect.topleft, view_offset)
        top_left_grid_pos = world_pos_to_grid_pos(top_left_world_pos)

        if current_top_left_grid_pos[0] != top_left_grid_pos[0] or\
                current_top_left_grid_pos[1] != top_left_grid_pos[1] or tile_selected:
            current_top_left_grid_pos = top_left_grid_pos
            sorted_sprite_list = SortableContainer((0, 0))
            bottom_right_grid_pos = world_pos_to_grid_pos([top_left_world_pos[0] + view_clip_rect.width,
                                                           top_left_world_pos[1] + view_clip_rect.height])
            bottom_left_grid_pos = world_pos_to_grid_pos([top_left_world_pos[0],
                                                          top_left_world_pos[1] + view_clip_rect.height])
            top_right_grid_pos = world_pos_to_grid_pos([top_left_world_pos[0] + view_clip_rect.width,
                                                        top_left_world_pos[1]])

            iStart = top_left_grid_pos[1] - 1
            jStart = top_left_grid_pos[0]
            iMax = bottom_right_grid_pos[1] + 5  # extend the effective clipping rectangle downward a couple of squares
            jMax = bottom_left_grid_pos[0] + 5   # this lets us handle objects 3x squares tall lazily
            jMin = top_right_grid_pos[0] - 1     # increasing this brings right edge in

            n = 0
            m = 1
            n_buffer = 1
            m_buffer = 0
            n_bump = False
            m_bump = False
            render_order = 0
            for i in range(iStart, iMax + 1):
                for j in range(jStart - n, jStart + m + 1):
                    for layer in range(0, number_visible_layers):
                        tile = tile_map[i][j][layer]
                        if tile is not None:
                            tile.render_order = render_order
                            sorted_sprite_list.add(tile.sprite)
                            render_order += 1
                if not n_bump:
                    n += 1
                    if (jStart - n) == jMin:
                        n_bump = True
                else:
                    if n_buffer > 0:
                        n_buffer -= 1
                    else:
                        n -= 1
                if not m_bump:
                    m += 1
                    if (jStart + m) == jMax:
                        m_bump = True
                else:
                    if m_buffer > 0:
                        m_buffer -= 1
                    else:
                        m -= 1
            sorted_sprite_list.add(player.sprite)
            sorted_sprite_list.sort_sprites()
        sorted_sprite_list.pos = view_offset  # set the camera position for the sprites

    background_sprite.render((0, 0))
    sorted_sprite_list.render()

    if time_delta > 0.0:
        if len(frame_rates) < 20:
            frame_rates.append(1.0 / time_delta)
        else:
            frame_rates.popleft()
            frame_rates.append(1.0 / time_delta)

        fps = sum(frame_rates) / len(frame_rates)
        fps_string = "FPS: " + "{:.2f}".format(fps)
        fps_test_render = fonts[0].render(fps_string, True, Color(255, 255, 255, 255))
        text_sprite = Sprite(renderer.load_texture(fps_test_render))
        text_sprite.render((600, 12))

    renderer.render_present()  # SDL_RenderPresent()
