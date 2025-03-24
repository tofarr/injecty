"""
Example demonstrating the logging functionality in injecty.
"""

import logging
from injecty import configure_logging, get_impls, get_default_impl, get_new_default_instance
from example.models.shape_abc import Shape

def main():
    # Configure logging at DEBUG level to see all log messages
    configure_logging(level=logging.DEBUG)
    
    print("Getting all shape implementations...")
    shapes = get_impls(Shape)
    print(f"Found {len(shapes)} shape implementations: {[s.__name__ for s in shapes]}\n")
    
    print("Getting default shape implementation...")
    default_shape = get_default_impl(Shape)
    print(f"Default shape implementation: {default_shape.__name__}\n")
    
    print("Creating a new instance of the default shape...")
    # This will fail because Shape is abstract, but the error will be logged
    try:
        instance = get_new_default_instance(Shape, permit_no_impl=True)
        print(f"Created instance: {instance}")
    except Exception as e:
        print(f"Error creating instance: {e}\n")
    
    # Try with a concrete implementation
    from example.models.circle import Circle
    
    print("Creating a Circle instance...")
    circle = Circle(radius=5.0)
    print(f"Circle area: {circle.area()}\n")

if __name__ == "__main__":
    main()