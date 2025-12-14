
import curses
import time
import textwrap

class CursesInterface:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.log_lines = []
        self.max_log_lines = 100
        self.input_buffer = ""
        self.cursor_pos = 0
        
        # Color initialization
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Normal Text / HUD
        curses.init_pair(2, curses.COLOR_CYAN, -1)    # Highlights / Headers
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Warnings / Attention
        curses.init_pair(4, curses.COLOR_RED, -1)     # Errors / Critical
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Special / CPU
        
        # Hide cursor initially (we might manage it manually or just let input line handle it)
        try:
            curses.curs_set(1)
        except:
            pass
            
        self.stdscr.nodelay(True) # Non-blocking input
        self.stdscr.keypad(True)
        
        # Window setup placeholders
        self.rows, self.cols = self.stdscr.getmaxyx()
        self.win_log = None
        self.win_status = None
        self.win_input = None
        
        self.resize()

    def resize(self):
        """Handle terminal resize."""
        self.rows, self.cols = self.stdscr.getmaxyx()
        self.stdscr.clear()
        self.stdscr.refresh()
        
        # Layout:
        # Header: Top 1 line (Managed by logic or just first line of log? Let's use stdscr for static header)
        # Log: Middle expandable
        # Status: Bottom fixed height (e.g. 8 lines)
        # Input: Bottom 1 line
        
        status_height = 8
        input_height = 1
        log_height = self.rows - status_height - input_height - 1 # -1 for header
        
        if log_height < 5:
            log_height = 5 # Minimum guarantee
            
        # Ref calculation
        # Header: Line 0
        # Log: Line 1 to 1+log_height
        # Status: Line 1+log_height to ...
        
        self.win_log_h = log_height
        self.win_log_w = self.cols
        self.win_log_y = 1
        self.win_log_x = 0
        
        self.win_status_h = status_height
        self.win_status_w = self.cols
        self.win_status_y = 1 + log_height
        self.win_status_x = 0
        
        self.win_input_h = input_height
        self.win_input_w = self.cols
        self.win_input_y = self.rows - 1
        self.win_input_x = 0
        
        # Re-create windows? subwin or newwin? newwin is safer for distinct updates
        # But efficiently we just track coords and refresh.
        # Actually initializing curses windows object is good for clipping.
        
        self.win_log = curses.newwin(self.win_log_h, self.win_log_w, self.win_log_y, self.win_log_x)
        self.win_log.scrollok(True)
        
        self.win_status = curses.newwin(self.win_status_h, self.win_status_w, self.win_status_y, self.win_status_x)
        
        self.win_input = curses.newwin(self.win_input_h, self.win_input_w, self.win_input_y, self.win_input_x)

    def draw_header(self):
        header_text = f"REACH CONNECTION CHECKER v1.0.0 | Uptime: {time.strftime('%H:%M:%S')} | Protocol: IPv4/v6 | Secure Mode: ACTIVE"
        # Pad with spaces
        header_text = header_text.ljust(self.cols)
        try:
            self.stdscr.addstr(0, 0, header_text[:self.cols], curses.color_pair(2) | curses.A_REVERSE)
        except curses.error:
            pass

    def log(self, message, color_pair_idx=1):
        """Add a line to the log window."""
        # Handle newlines in message
        lines = message.split('\n')
        for line in lines:
            self.log_lines.append((line, color_pair_idx))
            
        if len(self.log_lines) > self.max_log_lines:
            self.log_lines = self.log_lines[-self.max_log_lines:]
            
        # Draw log immediately? Or wait for refresh?
        # Let's just redraw log window contents
        self.render_log()

    def render_log(self):
        self.win_log.erase()
        
        # Calculate how many lines fit
        max_display_lines = self.win_log_h
        
        # We need to wrap lines if they are too long?
        # For simplicity, truncate or simple wrap handled by logic?
        # Let's just take last N entries.
        # Ideally we wrap text.
        
        display_queue = []
        for text, cpf in reversed(self.log_lines):
            # Wrap text
            wrapped = textwrap.wrap(text, self.cols - 1)
            if not wrapped: wrapped = [""]
            for w in reversed(wrapped):
                display_queue.insert(0, (w, cpf))
                if len(display_queue) >= max_display_lines:
                    break
            if len(display_queue) >= max_display_lines:
                    break
                    
        for i, (text, cpf) in enumerate(display_queue):
            try:
                self.win_log.addstr(i, 0, text, curses.color_pair(cpf))
            except curses.error:
                pass
                
        self.win_log.noutrefresh()

    def update_status(self, manager, cpu_agent=None, latency_check=False):
        self.win_status.erase()
        
        # Separator
        self.win_status.hline(0, 0, '-', self.cols, curses.color_pair(2))
        self.win_status.addstr(0, 2, " SYSTEM MEMORY DUMP ", curses.color_pair(2))
        
        # Hand Display
        # Format: [Index:CODE] ...
        # Color coding: Normal = Green, Highlight/Selected? No selection in CLI logic yet.
        
        # Hand lines
        hand_strs = []
        for idx, tile in enumerate(manager.get_hand()):
            code = manager.get_code(tile)
            hand_strs.append(f"[{idx}:{code}]")
            
        hand_line = " ".join(hand_strs)
        
        # Wrap hand line
        wrapped_hand = textwrap.wrap(hand_line, self.cols - 2)
        
        y_offset = 1
        for line in wrapped_hand:
            if y_offset < self.win_status_h - 1:
                self.win_status.addstr(y_offset, 1, line, curses.color_pair(1))
                y_offset += 1
                
        # Status info
        info_line_y = self.win_status_h - 2
        
        status_text = []
        if manager.is_reach:
             status_text.append("[!] LATENCY CHECK (CONTINUOUS PING) ACTIVE")
        else:
             status_text.append("STATUS: IDLE (WAITING Input)")
             
        if cpu_agent:
            # Maybe show minimal CPU info? Hidden usage?
            pass
            
        full_status = " | ".join(status_text)
        try:
            code = 3 if manager.is_reach else 1
            self.win_status.addstr(info_line_y, 1, full_status, curses.color_pair(code))
        except curses.error:
            pass
            
        self.win_status.noutrefresh()

    def render_input(self):
        self.win_input.erase()
        prompt = "ADMIN >> "
        self.win_input.addstr(0, 0, prompt, curses.color_pair(2) | curses.A_BOLD)
        self.win_input.addstr(0, len(prompt), self.input_buffer, curses.color_pair(1))
        
        # Move cursor
        try:
            self.win_input.move(0, len(prompt) + self.cursor_pos)
        except:
            pass
            
        self.win_input.noutrefresh()

    def refresh(self):
        self.draw_header()
        
        # We used noutrefresh on subwindows, now do doupdate
        curses.doupdate()

    def get_command(self):
        """
        Non-blocking check for input.
        Returns: 
           None if no full command yet.
           String command if Enter pressed.
        """
        try:
            ch = self.win_input.getch()
        except curses.error:
            return None
            
        if ch == curses.ERR:
            return None
            
        if ch == 10 or ch == 13: # Enter
            cmd = self.input_buffer.strip()
            self.input_buffer = ""
            self.cursor_pos = 0
            self.render_input()
            # Log the command echo
            self.log(f"ADMIN >> {cmd}", 1)
            return cmd
            
        elif ch == 8 or ch == 127 or ch == curses.KEY_BACKSPACE: # Backspace
            if self.cursor_pos > 0:
                self.input_buffer = self.input_buffer[:self.cursor_pos-1] + self.input_buffer[self.cursor_pos:]
                self.cursor_pos -= 1
        elif ch == curses.KEY_LEFT:
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
        elif ch == curses.KEY_RIGHT:
            if self.cursor_pos < len(self.input_buffer):
                self.cursor_pos += 1
        elif ch == curses.KEY_RESIZE:
            self.resize()
        elif 32 <= ch <= 126: # Printable
            char = chr(ch)
            self.input_buffer = self.input_buffer[:self.cursor_pos] + char + self.input_buffer[self.cursor_pos:]
            self.cursor_pos += 1
            
        self.render_input()
        return None

    def close(self):
        # Wrapper handles this usually, but good to have
        pass
