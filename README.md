# Rigid Packer
### Hierarchical Circle Packing with Real Time Dynamics

<img src='screen.png' alt='Screenshot' width='100%'>

<img src='demo.gif' alt='Demonstration' width='185' align='right' float='left'>

This script allows you to visualize any hierarchical data (in this case, [SQLite](https://sqlite.org/) database tables) in an intuitive way—using a circular treemap chart. Also, this script allows you to shift the leaves of a tree or entire subtrees with the mouse with saving the result.

The circle packing of the treemap chart is implemented in an original way—in real-time using rigid body physics (the [Box2D](https://github.com/pybox2d/pybox2d) engine is used). Natural packing instead of rigorous math makes hierarchy editing even more intuitive.

If desired, you can adapt this script to visualize and edit other hierarchical data structures by implementing a wrapper for them similar to the *storage.Storage* class.

The motive for creating this project is to do manual and automatic control of personal stuff using a database and an interactive chart as a client/editor.

## Requirements
1. [Python 3.7–3.8](https://www.python.org/downloads/)
1. `pip install -r requirements.txt`
   * [pybox2d](https://pypi.org/project/Box2D/) – physics engine
   * [PyQt5](https://pypi.org/project/PyQt5/) – GUI
   * [pygame](https://pypi.org/project/pygame/) – used for frame rate stabilization

## Usage
1. run *main.pyw*
1. shuffle items by `dragging` with mouse
1. `right click` on items to select it for picking or deselect
1. `double right click` on item with picked up sub-items to reset the selection
1. `double right click` on item without picked up sub-items to select or deselect for picking all items of same level
1. when any items are picked up, `left click` on another item to shake the picked up items into it
1. press `Escape` to quit
