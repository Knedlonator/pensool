#!/usr/bin/env python

import math
import coordinates
from gtk import gdk
import style
from decorators import *


def report_virtual():
  # During devt..
  import sys
  print "??? Override virtual method", sys._getframe(1).f_code.co_name


class Drawable(object):
  '''
  Things that can be drawn (glyphs and controls).
  
  DRAWING:
  See below draw()
  See below virtual method put_path_to() which distinguishes subclasses.
  
  SURFACES:
  Drawing is on a surface (device or file).
  Some of this is specific to a GUI surface (a display).
  Queries, such as is_inbounds() are for GUI's.
  
  CONTROL subclasses:
  Controls are specific to a GUI, but there is no reason
  controls could not be drawn to another surface.
  
  Some controls might not actually be drawn (the background manager), 
  but data is there to support it.
  
  COORDINATES:
  !!! Note these are all ideal coordinates, not inked coordinates.
  That is, model coordinates.
  FIXME
  '''
  
  def __init__(self, viewport):
    self._dimensions = coordinates.any_dims()
    self.viewport = viewport
    self.style = style.Style()
    self.filled = False

  
  '''
  Dimensions: GdkRectangle of dimensions in user coordinates.
  !!! These are the dimensions, not the bounds.
  The bounds of compound drawables is computed.
  !!! Copy, not reference, in case parameters are mutable.
  
  Note: this is a property. Properies are not polymorphic.
  Compound subclass of drawable override these by redeclaring dimensions
  as a property of Compound.
  '''
  def set_dimensions(self, dimensions):
    # Set a copy, not a reference
    self._dimensions = coordinates.copy(dimensions)
  def get_dimensions(self):
    # Return a copy, not a reference
    return coordinates.copy(self._dimensions)
  def del_dimensions(self):
    raise RuntimeError("Can not delete dimensions.")
  dimensions = property(get_dimensions, set_dimensions, del_dimensions, 
    "GdkRectangle of dimensions in user coordinates")


  def set_origin(self, coords):
    '''
    Set the origin part of the dimensions.
    That is, move without changing shape or size.
    No redraw.
    Note the origin has different meanings for different subclasses:
    it might be the upper left or it might be a hotspot or a center.
    TODO property
    '''
    self._dimensions.x = coords.x
    self._dimensions.y = coords.y
  
  def get_origin(self):
    # don't return a reference, return a copy
    return coordinates.UserCoords(self._dimensions.x, self._dimensions.y)

  
  def is_inpath(self, user_coords):
    '''
    Are coords in our path? (IE the edge)?
    Note user coords, not device coords.
    '''
    # TODO pass a context  .save() and restore()
    context = self.viewport.user_context()
    self.put_path_to(context)
    hit = context.in_stroke(user_coords.x, user_coords.y)
    return hit
  
  
  def is_inbounds(self, event):
    ''' Is the event in our bounding box?'''
    # Use intersection of rectangles.
    # Convert event point to rectangle of width one.
    return coordinates.intersect(self.get_bounds(), coordinates.coords_to_bounds(event))
  
  
  def center_at(self, event):
    '''
    Set ul at event.
    Center the bounding box at event.
    Assert bounding box is a rectangle.
    ??? Dimensions might not be a rectangle? TODO
    (No redraws)
    '''
    self._dimensions = coordinates.center_on_coords(self.get_bounds(), event)
    ###self._dimensions.x = event.x - (rect.width/2)
    ###self._dimensions.y = event.y - (rect.height/2)
  
  def move_absolute(self, event):
    '''
    Move origin absolute. Redraw.
    '''
    print "drawable.move_absolute", repr(self), "to ", event.x, event.y
    self.invalidate() # Schedule erase at old origin
    self.center_at(event)
    self.invalidate() # Schedule redraw at new origin


  def move_relative(self, event, offset):
    '''
    Move origin relative. Redraw.
    '''
    print "drawable.move_relative", repr(self), "by ", offset.x, offset.y
    self.invalidate() # Schedule erase at old origin
    self._dimensions.x += offset.x
    self._dimensions.y += offset.y
    self.invalidate() # Schedule redraw at new origin


  def get_bounds(self):
    '''
    Return rect of ideal bounding box.
    !!! Note path_extents is not ink, excludes the width of lines.
    Contrast to stroke_extents.
    '''
    context = self.viewport.user_context()
    self.put_path_to(context)
    extents = context.path_extents()
    # stroke_extents are float, avert deprecation warning
    # Truncate upper left via int()
    map(math.ceil, extents[2:3])  # ceiling bottom right
    int_extents = [int(x) for x in extents] 
    bounds = coordinates.dimensions_from_extents(*int_extents)
    # print "Bounds", bounds
    return bounds
  
    
  # TODO consolidate
  def get_inked_bounds(self):
    '''
    Return rect of inked bounding box in user coordinates.
    !!! Note stroke_extents includes the width of lines.
    '''
    context = self.viewport.user_context()
    self.put_path_to(context)
    extents = context.stroke_extents()
    # stroke_extents are float, avert deprecation warning
    # Truncate upper left via int()
    map(math.ceil, extents[2:3])  # ceiling bottom right
    int_extents = [int(x) for x in extents] 
    bounds = coordinates.dimensions_from_extents(*int_extents)
    # print "Bounds", bounds
    return bounds
 
      
  @dump_return
  def get_center(self):
    '''
    Compute center from components (not just center of self._dimensions!)
    Returns a dimensions! not a coordinates. ???
    Since objects may be laid out asymetrically,
    don't use this to get the origin !!!
    '''
    return  coordinates.center_of_dimensions(self.get_bounds())


  # Virtual methods
  '''
  Invalidate differs among subclasses:
  composite drawables: invalidate is aggregate
  primitive drawables: know their shape and may invalidate their shape, 
    but generally they invalidate a bounding box
  '''
  
  def invalidate(self):
    '''
    Virtual: each subclass knows whether it is inked and transformed,
    and thus how to invalidate the proper rectangle in the viewport.
    !!! Note this is only a concern for the viewport and not other device ports.
    '''
    raise NotImplementedError("Virtual")
  
  
  def is_in_control_area(self, event):
    '''
    Is the event in the hot area.
    Usually only for control subclass of drawable.
    '''
    raise NotImplementedError("Virtual")
    
    
  def put_path_to(self, context):
    '''
    Put path into context.
    Virtual: each subclass knows its own shape.
    '''
    raise NotImplementedError("Virtual")


  def orthogonal(self, point):
    '''
    Return an orthogonal unit vector at the given point on the boundary.
    Virtual: each subclass knows its own shape.
    '''
    print self
    raise NotImplementedError("Virtual")
    
    
    
    

  # Uncomment this to see drawables drawn.
  # @dump_event
  def draw(self, context):
    '''
    Draw self using context.
    '''
    # print "drawable.draw ", self.dump()
    self.style.put_to(context)
    self.put_path_to(context)
    if self.filled:
      context.fill()  # Filled, up to path
    else:
      context.stroke()  # Outline, with line width
    # Assert paths cleared from context

    
  def highlight(self, direction):
    '''
    Cause self to be temporarily drawn in the highlight style.
    Highlighting is a GUI focus issue, not a user document issue.
    '''
    self.style.highlight(direction)
    self.invalidate()
      
      
  def dump(self):
    return repr(self) + " " + repr(self._dimensions) 
    # print "Extents:", context.path_extents()
      

