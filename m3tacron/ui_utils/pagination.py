"""
Pagination Utilities.
"""
import reflex as rx

class PaginationMixin(rx.Mixin):
    """
    Mixin for states that need pagination.
    Assumes existence of a list to paginate or a total count.
    """
    page_size: int = 20
    current_page: int = 0
    
    # This should be overridden or computed by the state
    total_items_count: int = 0

    @rx.var
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total_items_count + self.page_size - 1) // self.page_size if self.total_items_count > 0 else 1

    @rx.var
    def has_next(self) -> bool:
        return self.current_page < self.total_pages - 1

    @rx.var
    def has_prev(self) -> bool:
        return self.current_page > 0

    def next_page(self):
        if self.has_next:
            self.current_page += 1
            self.on_page_change()

    def prev_page(self):
        if self.has_prev:
            self.current_page -= 1
            self.on_page_change()

    def set_current_page(self, page: int):
        self.current_page = page
        self.on_page_change()

    def on_page_change(self):
        """Hook for sub-classes to handle page changes (e.g. reload data)."""
        pass
