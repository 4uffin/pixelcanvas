# **PixelCanvas**

A simple, desktop-based pixel art editor built with Python and Tkinter. This application is designed for creating small-scale pixel art with a variety of tools and features.

## **Features**

* **Drawing Tools:** Includes a standard pixel brush, an eraser, and a powerful flood-fill tool.  
* **Color Palette:** A selection of predefined colors to get you started quickly.  
* **Image Brushes:** Use local image files as brushes to fill in the canvas.  
* **Project Management:** Save and load your projects as .json files to continue your work later.  
* **Exporting:** Export your finished pixel art as a high-quality PNG image.  
* **Usability:** Includes a toggleable grid overlay for precision, and a status bar for user feedback.

## Installation

Getting PixelCanvas up and running is a straightforward process. It's highly recommended to use a virtual environment to manage dependencies for your project.

### 1. Prerequisites

First, ensure you have Python 3.x installed on your system. You can verify your installation and version by running the following command in your terminal:

```python3 --version```

### 2. Create and Activate a Virtual Environment

Navigate to your project directory in the terminal. Then, create and activate a new virtual environment.

#### On macOS and Linux:

```python3 -m venv venv```
```source venv/bin/activate```

#### On Windows:

```python -m venv venv```
```venv\Scripts\activate```

### 3. Install Dependencies

With the virtual environment active, you can install all the required libraries listed in the requirements.txt file using pip.

```pip install -r requirements.txt```

## **How to Run**

Once the dependencies are installed, you can run the application from your terminal:

```python pixelcanvas.py```

## **License**

This project is open-source and available under the **MIT License**. For more details, see the LICENSE.md file.
