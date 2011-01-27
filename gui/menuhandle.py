#!/usr/bin/env python


'''
The Handle subclass of menu, i.e. a menu of type "handle menu".
See itemhandle.py for the handle subclass of menu item.
'''

import menu
import scheme
import base.vector as vector
import layout
from decorators import *
import config



class HandleGroup(menu.ItemGroup):
  '''
  Handle menu, layout is:
    moveable,
    layout reorients
    !!! only one item shown, as mouseovered
  '''
  
  @dump_return
  def new_layout_spec(self, event):
    """
    New layout_spec for a handle menu:
      vector is orthogonal to glyph
      benchmark is an offset from the glyph (so middle item is on glyph)
      opening item is the middle item
    
    Event opens the menu, here the event is a hit on a morph edge.
    TODO abstract opening with moving.
    """
    assert self.controlee
    
    """
    if self.controlee is scheme.model:
      # Handle menu opened on background, controls the document
      axis = vector.downward_vector()
    else:
    """
    # axis is orthogonal to controlee.
    # Controlee is usually a graphic morph or background.
    axis = self.controlee.get_orthogonal(event)
      
    benchmark = layout.benchmark_from_hotspot(axis, event)
    
    # FIXME hardcoded to open at 1, should be the middle of the menu
    self.layout_spec = layout.LayoutSpec(event, benchmark, axis, opening_item=1)
    return self.layout_spec # for debug
    
    """
    FIXME center on event, and open on middle item, benchmark away from hotspot
    # center menu on the edge of controlee
    # center is intersection of orthogonal and controlee edge
    ray tracing algorithm
    # benchmark: from center proceed half menu length in direction of orthogonal
    """
    
  @dump_event
  def layout(self, event=None):
    '''
    Layout (position) all items in group.
    
    For Handle Menu:
      In line orthogonal to glyph.
      Ordered towards center of glyph (anti direction of orthogonal vector.)
      Overlapping items.
    
    A handle group lays out all items even though only one is shown.
    When exit an item, other items are already laid out.
    
    Using transforms, a menu only needs to be layed out once.
    A change to layoutspec can require updates to the transform or the layout.
    '''
    point = vector.Point(0,0)
    for item in self:
      item.center_at(point)
      # Next item along a line (the x-axis).
      # FIXME more generally, get the size of an item
      # point.y += item.get_dimensions().height
      point.x += config.ITEM_SIZE/2 # HEIGHT?
    """
    point = vector.Point(0,0)
    
    ## TODO ??? is this is in spec?
    ## layout_vector = self.controlee.get_orthogonal(event)
    ## FIXME is event ever passed?
   
    # FIXME Offset by half count of items
    point.x += self.layout_spec.vector.x * config.ITEM_SIZE/2
    point.y += self.layout_spec.vector.y * config.ITEM_SIZE/2
    
    for item in self:
      item.center_at(point)
      # Space next item along vector
      # FIXME more generally, get the size (width, height) of an item
      # point.y += item.get_dimensions().height
      point.x -= self.layout_spec.vector.x * config.ITEM_SIZE/2
      point.y -= self.layout_spec.vector.y * config.ITEM_SIZE/2
    """
    """
    OLD untransformed.
    
    # Center first item on benchmark.  Ignore the event.
    ## OLD temp_rect = coordinates.dimensions(event.x, event.y, 0, 0)
    ### !!! This causes a seg fault temp_rect = copy.copy(self.layout_spec.benchmark)
    temp_rect = self.layout_spec.benchmark.copy()
    '''
    # get vector for direction of menu: orthogonal to the controlee eg glyph
    layout_vector = self.controlee.get_orthogonal(event)
    self.layout_spec.vector = layout_vector  # Remember it, items can ask for it
    '''
    layout_vector = self.layout_spec.vector.copy()
    
    # layout all items
    for item in self:
      item.center_at(temp_rect)
      ''' Dumbed down version
      # Layout next item leftward
      temp_rect.x -= item.dimensions.width/2
      '''
      # Multiply unit ortho vector by dimension vector; add/sub to previous coords
      # FIXME vector scale, translate
      temp_rect.x -= self.layout_spec.vector.x * item.get_dimensions().width/2
      temp_rect.y -= self.layout_spec.vector.y * item.get_dimensions().height/2
    print "returned from layout", self.layout_spec
    """
      
  @view_altering
  @dump_event
  def slide(self, pixels_off_axis):
    '''
    Slide menu substantially orthogonal to original axis.
    Substantially means: follow a curve.
    
    By magnitude pixels_off_axis
    in angle left or right indicated by sign of pixels_off_axis.
    
    !!! Does not layout menu's items: self.layout() 
    '''
    ## OLD layout.slide_layout_spec(self.layout_spec, pixels_off_axis)
    # Update the layout spec
    layout.slide_layout_spec_follow(self.controlee, self.layout_spec, pixels_off_axis)
    # Reposition: update the menu's transform
    self.position()

  @transforming
  def draw(self, context):
    '''
    Draw Handle Menu.
    Specializes Menu: only draw the current item.
    !!! Overrides composite.draw() (but follows the template.)
    '''
    self.style.put_to(context)
    # !!! Only draw one of my items.
    self.bounds = self[self.active_index].draw(context)
    return self.bounds
 
