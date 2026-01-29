"""
Pagination Utilities.
"""
import reflex as rx

class PaginationMixin(rx.State):
    """
    Mixin for states that need pagination.
    Assumes existence of a list to paginate or a total count.
    """
    page_size: int = 20
    current_page: int = 0
    total_items_count: int = 0
    
    @rx.var
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_items_count + self.page_size - 1) // self.page_size if self.total_items_count > 0 else 1

    @rx.var
    def has_next(self) -> bool:
        """Helper for UI disabling."""
        return self.current_page < self.total_pages - 1

    @rx.var
    def has_prev(self) -> bool:
        """Helper for UI disabling."""
        return self.current_page > 0

    def next_page(self):
        """Handle next page click."""
        # Inspection check: if current_page is a Var, it will fail comparison or have no value
        print(f"DEBUG: next_page called. current_page={self.current_page} (type={type(self.current_page)})")
        if isinstance(self.current_page, (int, float)):
            self.current_page += 1
            print(f"DEBUG: next_page incremented. new page={self.current_page}")
            return self.on_page_change()
        else:
             print("DEBUG: current_page is not int/float!")
        return []

    def prev_page(self):
        """Handle prev page click."""
        print(f"DEBUG: prev_page called. current_page={self.current_page} (type={type(self.current_page)})")
        if isinstance(self.current_page, (int, float)) and self.current_page > 0:
            self.current_page -= 1
            print(f"DEBUG: prev_page decremented. new page={self.current_page}")
            return self.on_page_change()
        return []

    def set_current_page(self, page: int):
        """Set page directly."""
        if isinstance(self.current_page, rx.Var): return []
        self.current_page = page
        return self.on_page_change()

    def jump_to_page(self, page_str: str):
        """Handle manual page input."""
        try:
            p = int(page_str)
            # Convert 1-based input to 0-based index
            idx = p - 1
            if 0 <= idx < self.total_pages:
                self.current_page = idx
                return self.on_page_change()
        except ValueError:
            pass

    def on_page_change(self):
        """Hook for sub-classes to handle page changes (e.g. reload data)."""
        return []
