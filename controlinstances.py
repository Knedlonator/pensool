#!/usr/bin/env python

'''
Builds controls for the app.
'''

import gui.menu
import gui.itemmenu
import gui.itemhandleline
import gui.itemhandlecoords

def build_handle_menu(viewport):
  '''
  '''
  handle_group = gui.menu.HandleGroup(viewport)
  handle_control = gui.itemhandleline.LineHandleItem(viewport)
  handle_group.add(handle_control)
  handle_control = gui.itemhandlecoords.MoveHandleItem(viewport)
  handle_group.add(handle_control)
  handle_control = gui.itemhandlecoords.ResizeHandleItem(viewport)
  handle_group.add(handle_control)
  return handle_group
  

def build_popup_menu(viewport):

  menu_item = gui.itemmenu.SquareMenuItem(viewport)
  menu_item2 = gui.itemmenu.SquareMenuItem(viewport)
  menu_item3 = gui.itemmenu.SquareMenuItem(viewport)

  menu_group = gui.menu.MenuGroup(viewport)
  menu_group.add(menu_item)
  menu_group.add(menu_item2)
  menu_group.add(menu_item3)
  return menu_group

