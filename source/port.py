''' Port class '''
'''
Copyright 2010, 2011 Lloyd Konneker

This file is part of Pensool.

Pensool is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
'''

import pygtk
import gtk
import cairo  # for gtk drawing surface (pango is built in)
import pangocairo # for print and save surfaces
import os
import gui.manager.handle
import style
import base.vector as vector
from decorators import *
import base.alert as alert
import config

import logging
my_logger = logging.getLogger('pensool')

class Port(object):
  '''
  Traditional meaning: drawing area (rectangle) on surface
  
  Draws model on surface
  
  The different subclasses differ in the way they treat an infinite model:
    views pan and scroll a window over it
    printerports paginate it
    fileport saves whole model
  
  Also differ in what extras (in excess of the model) might be drawn:
    a view also draws controls
    a printerport also draws page headers etc.
    a fileport might have extra data
  '''
  def __init__(self):
    self.model = None
    pass
    
  def set_model(self, model):
    self.model = model
    
  # @dump_event
  def draw_model(self, context):
      self.model.draw(context)
      # Not all ports draw control widgets
    
  
class ViewPort(Port):
  '''
  A Port on a display device (screen, monitor).
  
  Understands that controls (widgets) drawn also.
  
  A ViewPort is a window in a display.
  EG surface is a window, view defines the being-viewed rect on the doc.
  
  A transform from doc(user) to device coords defines the view.
  The scheme is a transformer, not a port.
  The viewing transformation is the top transform in the scheme's hierarchical model.
  
  Conceptually, fundamental operations on a view:
    Operation on the documents under (in) the port (see scheme):
      scroll (pan)
      zoom (on a point)
    Operation on the port itself are handled by the window manager:
      move, resize, close, minimize
  '''
  
  
  def __init__(self, da):
    # formerly subclassed: gtk.DrawingArea.__init__(self)
    da.connect("expose_event", self.expose)
    
    # TODO scraps for a pixbuf background
    # global pb
    # self.connect_after('draw_background', self.draw_background, pb)
    
    self.surface = da.window
    self.da = da
    # self.da.set_double_buffered(False)  # for animation TODO
    Port.__init__(self)
    self.style = style.Style()
  
  
  # TODO this might not be used
  # The alternative is to invalidate the scheme, which might be a smaller rect
  def invalidate(self):
    """ Queue expose event on entire port window"""
    self.surface.invalidate_rect(self.da.allocation, False)
  
    
  def expose(self, widget, event):
    '''
    Draw things: model and control groups
    '''
    # print "Expose ************* area", event.area
    '''
    !!! Note that due to double-buffering, 
    Cairo contexts created in a GTK+ expose event handler cannot be cached 
    and reused between different expose events.
    '''
    # TODO event.area to clipping in context
    context = self.da.window.cairo_create()
    x1, y1, x2, y2 = context.clip_extents()
    # print "Clipping: UCS", x1, y1, x2, y2, "DCS", context.user_to_device(x1,y1), context.user_to_device(x2,x2)
    # print "Matrix: ", context.get_matrix()
    self.style.put_to(context)
    
    # Draw ephemeral controls untransformed
    for widget in config.scheme.widgets:
      widget.draw(context)
      
    # Draw model and persistent controls in transformed coords
    # view has no transformation.
    # The top level of the scheme has the viewing transformation.
    ## OLD context.set_matrix(self.matrix)
    config.scheme.transformed_controls.draw(context)
    self.draw_model(context)
    
    gui.manager.handle.draw()  # Draw handle set for any current morph

  
  def user_context(self):
    # Return a context in user coords ie doc
    return self.da.window.cairo_create()
  
  def controls_context(self):
    # Return a context for drawing controls
    return self.da.window.cairo_create()

  # The UCS is the coordinate system at the scheme and model level.
  # Each submorph is in it's own coordinate system.
  
  
  def device_to_user(self, x, y):
    '''
    Transform coordinates from device DCS to user UCS.

    From cairo docs:
    context.device_to_user() returns tuple (float, float)
    Transform a coordinate from device space to user space 
    by multiplying the given point by the inverse of the current transformation matrix (CTM).
    '''
    context = self.user_context()
    ### context.set_matrix(self.matrix)
    return vector.Vector(*context.device_to_user(x, y))

"""    
  def user_to_device(self, x, y):
    context = self.user_context()
    ### context.set_matrix(self.matrix)
    return vector.Vector(*context.user_to_device(x, y))



  def device_to_user_distance(self, x, y):
    '''
    Transform a pair of distances from device to user coords.
    Return type:	(float, float)
    See cairo docs
    '''
    context = self.da.window.cairo_create()
    ### context.set_matrix(self.matrix)
    return vector.Vector(*context.device_to_user_distance(x, y))
    
  def user_to_device_distance(self, x, y):
    context = self.da.window.cairo_create()
    ### context.set_matrix(self.matrix)
    return vector.Vector(*context.user_to_device_distance(x, y))
"""


class PrinterPort(Port):
  '''
  A Port on a printer-like device
  
  Understands pagination.
  '''
  def __init__(self):
    self.settings = None
    Port.__init__(self)
    
  def begin_print(self, operation, print_context):
    # TODO divide the model into pages
    operation.set_n_pages(1)
  
  def draw_page(self, operation, print_context, page_number):
    ''' On a printer '''
    context = print_context.get_cairo_context()
    self.draw_model(context)
    
  def do_print(self, *args):
    # print_op is ephemeral 
    print_op = gtk.PrintOperation()

    if self.settings != None: 
      print_op.set_print_settings(self.settings)

    print_op.connect("begin_print", self.begin_print)
    print_op.connect("draw_page", self.draw_page)

   
    # Second parameter is the parent widget of the print dialog.
    # Here None means top level, ie not a child of the app window or view.
    # port.surface did not work.
    res = print_op.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, None)
    
    # Signals are emitted here at the conclusion of the print dialog

    if res == gtk.PRINT_OPERATION_RESULT_APPLY:
        self.settings = print_op.get_print_settings()
    
    
    
    
class FilePort(Port):
  '''
  A Port on a file-like device
  
  Understands what file formats we support,
  there is a different surface for each format.
  '''
  def __init__(self):
    self.settings = None
    Port.__init__(self)
  
  
  def _context_for_surface(self, surface):
    '''
    Note: GTK functions return a context that is Pango.
    For other surfaces, you must get a cairo.Context(),
    then turn it into a pangocairo.CairoContext().
    IOW GTK surfaces yield contexts that support drawing text using pango,
    but ordinary cairo.Contexts do NOT.
    '''
    return pangocairo.CairoContext(cairo.Context(surface))


  def do_save(self, * args):
    filename = self.ask_save_filename()
    # TODO other surfaces png, svg, pdf
    if filename is not None:
      save_file, extension = os.path.splitext(filename)
      
      try:
        if extension == ".svg":
          surface = cairo.SVGSurface(filename, 200, 200)
          self.draw_model(self._context_for_surface(surface))
          # Note differs from png: no write_to_svg()
        elif extension == ".png":
          surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 200, 200)
          self.draw_model(self._context_for_surface(surface))
          try:
            surface.write_to_png(filename)
          except IOError:
            alert.critical_dialog("IO error.")
            return
        # width_in_points, height_in_points)
        else:
          alert.warning_dialog("Unsupported file extension: " + extension)
          my_logger.debug("Unsupported extension.")
          return
      except MemoryError:
        alert.critical_dialog("Out of memory.  You should save and restart now.")
        return
      surface.finish()
      my_logger.debug("File saved.")
    
    
  def ask_save_filename(self):
    
    if gtk.pygtk_version < (2,3,90):
      alert.critical_dialog( "PyGtk 2.3.90 or later required" )
      return None
   
    dialog = gtk.FileChooserDialog("Save..",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_SAVE,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
   
    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)
    
    filter = gtk.FileFilter()
    filter.set_name("Images")
    filter.add_mime_type("image/png")
    filter.add_mime_type("image/svg")
    filter.add_mime_type("image/pdff")
    filter.add_pattern("*.png")
    filter.add_pattern("*.svg")
    filter.add_pattern("*.pdf")
    dialog.add_filter(filter)
    
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
      filename = dialog.get_filename()
    elif response == gtk.RESPONSE_CANCEL:
      filename = None
    dialog.destroy()
    return filename


# Singleton, set when app starts
view = None
