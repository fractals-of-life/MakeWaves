r"""Usage: 
      $ python_2.7.10 draw_wave_tex.py <input_file>.csv <output_file>.tex  <scale=4|2|1>
"""

import sys
import re
import subprocess
import logging

if (float(sys.version_info[0]*10000)
         + float(sys.version_info[1])*100
         + float(sys.version_info[2])) < 20710:
   raise Exception("Blaaast! Python 2.7.10 is required")

# ------------------------------------------------------------------------------
# For the moment logging is not controlled from the command line.
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)-10s %(lineno)5d] %(funcName)20s(): %(message)s"
    )
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# TEX Syntax notes:
# o Use S for a space or use ;[dotted][L,H,X]; for a dotted representation of
# continuity
# o Tex timing is clock pulse wide.
# ------------------------------------------------------------------------------
def restore_after_spacer(state_min1, state_min2):
    """Return the state before spacer as continuation

    state_min1 : Holds the sated from the renderd signal imm preceeding current.
    state_min2 : Holds the state 2 steps ahead of current.

    Note that the backward search is to establish continuation, becaue by
    nature in the XL we only capture Value changes. So when a break is placed
    in the waveform we need to performa  backward search to establish the
    last stable value.
    """
    logger.debug('t-2 : {0} t-1 : {1}'.
                format(state_min2, state_min1) 
                )

    wave_state = '';
    # Bug Fix: Issue 1.
    # Search backwards. If t-1 was a spacer, then use t-2 for continuation
    if (re.search('\bS\b|\[dotted\]', state_min1)):
        wave_state = state_min2 
    else:
        wave_state = state_min1 

    # Flag erraneous input
    if (re.search('\bS\b|\[dotted\]', wave_state)):
        logger.error('Not supported, Possible back to back breaks or break on first clock')

    wave_state = re.sub(r'(\d+[UDXLHCudxlhc])(.*)',r'\1', wave_state)

    return wave_state

# ------------------------------------------------------------------------------
# generic single bit signal
# ------------------------------------------------------------------------------
def add_signal(signal_array, json_file, indent_level, scale):
    """Add  a single bit signal to waveform except clock

    This is the default as the single bit signals have no prefix or
    reserved name.

    signal_array    : is the raw signal array which is a line from the CSV.
    json_file       : this is the TEX file handler, into which rendered signal
                    will be written
    indent_level    : This is the indent level to use in the tex file for
                    readability.
    scale           : This is the scale for drawing out the waveforms. This is
                    passed down from the command line of this script. 


    The following wxpansion will be done assuming Scale = 4
    0    -> 4L
    1    -> 4H
    X/x  -> 4X
    G    -> 4*0.03T 4*0.97T; A glitch showing up on last level., where T is
            Toggle in TEX
    0.x  -> 0.25*4U 0.75*4L; an undef lasting 0.25 of a cycle followed by Hig;  
    -0.x -> 0.25*4U 0.75*4H; an undef lasting 0.25 of a cycle followed by Low;
    |    -> ;dotted]2<val_b4_break> ; draws a dotted continuation, L H, U etc
    """

    logger.debug('+ Raw signal:{0}'.format(signal_array))

    initial_val = signal_array[1]
    # If no intial condition is defined give it an X, saves headache later. 
    # issue a warning.
    if ( not(re.search('^[01xX]', signal_array[1])) ):
        signal_array[1] = str(scale) +'X'
        logger.warning(
                '+ Initial condition not defined for {0}. Force invalid \'x\''
                .format(signal_array[0])) 
    for i,time_step in enumerate(signal_array[1:]):

        logger.debug('|---:{0} {1}'.format(i, time_step))

        if (re.search('X|x',time_step)):
            signal_array[i+1] = str(scale) + 'X'
        # FIXME: New not in documentation.
        # This is added to represent glitchiness or uncertanity.
        elif (re.search('G',time_step)):
            signal_array[i+1] = str(scale*.03) + 'T' + str(scale*.97) + 'T'
        # FIXME: New not in documentation
        # this is a simple encoding. 0.x will indicate a undef to 1 transition which
        # is not full cycle, and -0.x will show a undef to 0 transition
        # can potenitally be expanded to use x to decide proportion.
        # The combo indication is fixed to 0.25
        elif (re.search(r'0.\d',time_step)):
            if (re.search(r'-0.\d',time_step)):
                signal_array[i+1] = str(0.25*scale) + 'U' + str(0.75*scale) + 'L'
            else:
                signal_array[i+1] = str(0.25*scale) + 'U' + str(0.75*scale) + 'H'
        elif (re.search('0',time_step)):
            signal_array[i+1] = str(scale) + 'L'
        elif (re.search('1',time_step)):
            signal_array[i+1] = str(scale)+'H'
        elif (re.search('\|', time_step)):
            signal_array[i+1] = 'S'
            temp = re.sub(r'\d+([UDXLHC]).*',r'\1',signal_array[i])
            signal_array[i+1] = ';[dotted]2' + temp + ';'
        else:
            # allow us to deal with a value change format by searching
            # backwards to find the last change from the current time step. The
            # search is to be perfromed on the waveform rendered so far.
            signal_array[i+1] = restore_after_spacer(signal_array[i],signal_array[i-1]) 

    return signal_array

# ------------------------------------------------------------------------------
# generic clock signal
# ------------------------------------------------------------------------------
def add_clock(signal_array, json_file, indent_level, scale, clock_edges):
    """ clock signal

    signal_array    : The raw csv line
    json_file       : output file
    indent_level    : was used for adding a indent level to tex_blk
    scale           : global waveform scale.
    clock_edges     : A list of clock_edges as the clock is processed
                        This will be used for drawing edge lines later.

    """

    logger.debug('+ parsing clock {0}'.format(signal_array))

    # Clock name format check: Cxx:(n?)clk_name
    # Cxx, where xx is the duty cycle of the clock
    # (n?) denotes if it is a ngeative clock or not. Example C25:nclk1,
    # C10:clk2 etc.
    # Wont reach here because not recognised as a clock..
    # FICME catch C100, C1 etc type errors
    if not(re.search(r'^C\d+',signal_array[0])):
            raise TypeError('Incomplete clock name, see template')
    # why are we doing it this way rahter than using a dict.
    # Ans: to preserve ordering, Apparently in later versions of python this is
    # fixed.
    labeled_edges = [];
    if (re.search(':n[cC]',signal_array[0])):
        initial_val = 0 
    else:
        initial_val = 1 

    # The way the dotted continuation is inserted below will not work for negedge
    # clocks.
    clk_name = re.sub(r'^.*:','',signal_array[0]) 
    clk_name = re.sub(r'\\_', '', clk_name)

    # Extract clock duty cycle from name. The syntax for this in the excel is
    # C25 : <clkname> 
    # Extract the number before C to work out the duty cycle. 
    clock_duty = signal_array[0] 
    clock_duty = re.sub(r'^C(\d+):.*', r'\1', signal_array[0])
    clock_duty = float(clock_duty)/100;
    clock_template = '{0}C {1}C'.format(clock_duty*scale, (1-clock_duty)*scale) 
    # Used to count transitions in terms of scale.
    last_mark = 0
    for i,time_step in enumerate(signal_array[1:]):

        # Flag Source error: 
        if (not(re.search(r'\d+|G|\|', time_step))):
            logging.error('Found undefined clock after {0} at column {1}'.format(signal_array[i], i+1))
            logging.error('    All clocks need to be uniquely marked with a cycle # number or G where gated')
            raise ValueError('Unexpected or blank clock label')

        labeled_edges = []

        # how to deal with a break. the break is .5 of a full cycle or scale/2
        # So after a break the clock will be inverted i.e half cycle.
        # The half cycle break is deliberate to save space.
        if (re.search('^\|', time_step)):
            signal_array[i+1] = 'S'
            temp = re.sub(r'\d+([UDXLHC]).*',r'\1',signal_array[i])
            # represent the break as high or low depending on the initial value
            # of clock ie posedge or negedge.
            if (initial_val):
                signal_array[i+1] = ';[dotted]' + '2L;'
            else:
                signal_array[i+1] = ';[dotted]' + '2H;'
            
            # FIXME this is hardcoded to 2, and so is every ;dotted break
            # Ideally should use scale/2
            last_mark = last_mark + 2 

        elif (re.search('G',time_step)):
            # Again the sense of clock derived from its name is used to
            # implement the gated state, ie low for a posedge, and high for a
            # negedge
            if (initial_val):
                signal_array[i+1] = str(scale)+'L'
            else:
                signal_array[i+1] = str(scale)+'H'

            last_mark = last_mark + scale

        else:
            # A clock cycle number can be negative.
            signal_array[i+1] = re.sub(r'^(-?\d+).*', r'\1)', signal_array[i+1])
            signal_array[i+1] = 'N(' + clk_name + signal_array[i+1]
            # Capture every edge with its unique node name into labeled_Edges.
            # This will be used later for drawing edges.
            labeled_edges.append(signal_array[i+1])
            signal_array[i+1] = signal_array[i+1] + clock_template 
            labeled_edges.append(str(last_mark))
            clock_edges.append(labeled_edges)
            last_mark = last_mark + scale 

    # Decide posedge or negedge clock based on clock name. 
    # negedge version should strictly start with nclk or nClk names
    if (initial_val):
        signal_array[1] = '[C] ' + signal_array[1]
    else:
        signal_array[1] = '' + signal_array[1]

    return signal_array

# ------------------------------------------------------------------------------
# generic multi bit signal
# EDIT:28062018 
# Have noe removed fill=none and replaced with ';' at all instances to reset
# fromat to default
# ------------------------------------------------------------------------------
def add_bus(signal_array, json_file, indent_level, scale):
    initial_val = signal_array[1]
    reset_fill = 0
    # Force an initial value if none defined, to prevent down stream errors.
    if (re.search('^$',initial_val)):
        initial_val = str(scale) + 'U';
        signal_array[1] = 'U'
        logger.warning(
            '+ Initial condition not defined for {0}. Force Undef'
            .format(signal_array[0])
        )

    previous = initial_val
    
    for i,time_step in enumerate(signal_array[1:]):
        # Extract the annotation for data whcich is of the form
        # <some text>[c:g] where some text becomes the displayed data and the
        # colour defined by c:[o|r|g|b] is the colour of the valid data bus
        # cycle. The search is captured to tag for later use.
        # Extract field1:field2, where field1 is the annotation and field 2 = [c:.]
        # forms the cell decoration.
        tag =  (re.search(r'((?i)[a-z 0-9_+-:*()=]+)(\[(c:[orgb])\])?',time_step))
          
        if (re.search('^[xX]$',time_step)):
            signal_array[i+1] = ';' + str(scale) + 'X'
        elif (re.search('^[uU]$',time_step)):
            signal_array[i+1] = ';' + str(scale) + 'U'
        # Here , if tag is non empty we assume a valid dtat value is defined.
        elif (tag):
            if tag.group(2):
                color = tag.group(3).split(':') # unused
                if (re.search('o', color[1])):
                    fill = '[fill={rgb,255:red,255; green,204; blue,153}]'
                    reset_fill = 1
                elif(re.search('r', color[1])):
                    fill = '[fill={rgb,255:red,255; green,102; blue,102}]'
                    reset_fill = 1
                elif(re.search('g', color[1])):
                    fill = '[fill={rgb,255:red,204; green,255; blue,102}]'
                    reset_fill = 1
                elif(re.search('b', color[1])):
                    fill = '[fill={rgb,255:red,153; green,204; blue,255}]'
                    reset_fill = 1
            else:
                fill = ''
                  
            # Required to reset theme
            # However there is an easier method which is by placing a ';' to
            # terminate use of a theme. Investigate.
            if (reset_fill and format(tag.group(1)) and not(fill)):
                reset_fill =0 
                #fill = '[fill=none]'
                # The use of ; seems to work, i.e it resets the formatting to
                # default
                fill = ';'

            previous = str(scale) + 'D' + fill

            # Underscores are commonly used in signal names, but used within a bus
            # node text, it causes wild tex errors. So escape it
            signal_array[i+1] = fill + str(scale) + 'D{{{0}}}'.format(re.sub(r'_', r'\\_',tag.group(1)))


        elif (re.search('^\|$', time_step)):
            # Extract type along with decoration for use in dotted.
            temp = re.sub(r'(?:\[.*\])?\;?\d+([UDXLHC]).*',r'\1',signal_array[i])
            signal_array[i+1] = ';[dotted]2' + temp + ';'

        else:
            signal_array[i+1] = restore_after_spacer(signal_array[i],signal_array[i-1]) 
            # NOTE: What is this circus for.
            # when tex renders the waveform, it extents TAG backwards.. right to left 
            # ie 2D 2D{TAG} 2D 
            # |   TAG   |   |
            # In our source XL, we record data only when it changes, i.e left
            # to rt so the prev data has to be extended just before the change.
            # In natural order tex would fail to do so. So the last change with
            # tag is exchanged on every clock if Exel has empty cells or intent
            # is continuation.
            # TODO: If two cells have the same TAG and have no other tags inbetween
            # then the transition can be removed for a cleaner waveform.
            # Bug Fix: Issue 1
            if (re.search('\bS\b|\[dotted\]', signal_array[i])):
                temp = signal_array[i+1]
                signal_array[i+1] = signal_array[i-1]
                signal_array[i-1] = temp
            else:
                temp = signal_array[i+1]
                signal_array[i+1] = signal_array[i]
                signal_array[i] = temp

    return signal_array

# ------------------------------------------------------------------------------
# add a marker/spacer line 
# ------------------------------------------------------------------------------
def add_marker(signal_array, json_file, indent_level, scale):
    for i,time_step in enumerate(signal_array[1:]):
        # FIXME : Check why is there a '^' . has it seeped in from a preve
        # version
        if re.search('[^>]', time_step):
            signal_array[i+1] = ' N('+ time_step + ')'
    return signal_array

# ------------------------------------------------------------------------------
# adding groups to label waveforms
# ------------------------------------------------------------------------------
def add_grp(signal_array, json_file, indent_level, scale):
    logging.info('Adding a group sepeartor')
    # Prevent counting of markup.
    temp = re.sub(r'\<.*','', signal_array[0])
    # Prevent counting of escaped chars.
    temp = re.sub(r'\\','', temp)
    length_str = 20 - len(temp);
    # allowed in group name @ to specify a location, alphanumeric, \_
    signal_array[0] = re.sub(r'(^G:[\\@\w\-]*)(<.*$)?',r'\1<b>', signal_array[0])
    logger.debug('Sanitized group header{0}'.format(signal_array[0]))
    signal_array[0] = (length_str*'\_') + signal_array[0] 
    if (length_str < 1):
        logging.warning('Too many chars in label{0} {1}'.format(length_str, temp))
    signal_array[1:] = [ str(scale) +'L' for j in signal_array[1:]] 

# ------------------------------------------------------------------------------
# dump wave block
# ------------------------------------------------------------------------------
def dump_timingtable(timing_block, json_file , indent_level): 
    # to allow merging of the markers which are always placed below the signal 
    i = 0;
    accumulate = 0
    output =0 
    temp = []
    # USe this to capture the state preceding the marker. This allows us to pick
    # sane anchor points for drawing arcs
    marked_edges = {}
    while (i < len(timing_block)):
        signal_array = timing_block[i]
        i += 1
        # FIXME: What is this mess
        # What is required is to merge the current line and any subsequent lines
        # starting with a M: but before another signal line so that markers are
        # placed appropriately in the tex representaion. The utility of multiple
        # lines of markers for a single signal is not great, but just coded as a
        # safegaurd. This imposes the condition that marker lines be consumed until
        # another valid signal defenition is detected. 
        # TODO: The following code is not very elegant. consider rewriting 
        if (len(signal_array) > 1):
            if (re.search('^M:', signal_array[0])):
                signal_array[0] = ''
                #temp  = [m+n for m,n in  zip(temp,signal_array)]
                accumulate = 1
                output =1 
                # temp holds the current accumulated signal,
                # look at the next line, if it is also a marker then keep
                # merging ..ie multiple rows collapsed into 1, combined
                # columnwise.
                for j,(m,n) in enumerate(zip(temp,signal_array)):
                    if (n):
                        # Skip a Spacer char on M:. This makes it easier to draw spacers
                        n = re.sub('\|','',n)
                        # collapse rows columnwise.
                        temp[j] = m+n
                        # extract state of wave at marker. 
                        m = re.sub(r'.*(\d+[DULHXCdulhxc]).*', r'\1', m)
                        edge = [m,m]
                        if (j < len(temp)):
                            next_state = temp[j+1]
                            next_state = re.sub(r'.*(\d+[DULHXCdulhxc]).*', r'\1', next_state)
                            edge = [m,next_state]

                        # for the marked edge, we capture the prev and next
                        # state . This dict will be used by the add_arrows
                        # section to draw approproitate arrows.
                        marked_edges.update({n:edge})

            else:
                # The merged prev marker row and signal not printed yet.
                # But now a new signal has been found hence no more merging.
                if (output):
                    json_file.write('{2}{0:25s} & {1} \\\\\n'.format(temp[0], ' '.join(temp[1:]),''.join(indent_level)))
                    accumulate = 0
                    output = 0 
                # the heading row or the actual signal row
                if not(accumulate):
                    temp = signal_array
                    accumulate = 0 
                    output = 1 

        else:
                if (output):
                # Not a signal but empty line
                # The merged prev marker row and signal not printed yet.
                # But now a new signal has been found hence no more merging.
                    json_file.write('{2}{0:25s} & {1} \\\\\n'.format(temp[0], ' '.join(temp[1:]),''.join(indent_level)))

                output = 0
                accumulate = 0
                json_file.write('{0}\\\\\n'.format(''.join(indent_level)))

    return marked_edges

# ------------------------------------------------------------------------------
# UNUSED
# ------------------------------------------------------------------------------
def add_notes(signal_array, json_file, indent_level):

    logger.debug('+ Create notes') 
    # add the NOTES grabbed from CSV
    json_file.write('{0}foot: {{ text:\n'.format(''.join(indent_level)))
    #indent_level.append('  ')
    json_file.write('{0}[\'tspan\',\n'.format(''.join(indent_level)))
    #indent_level.append('  ')
    json_file.write('{0}[\'tspan\', {{ class:\'h6\' , \'text-anchor\':\'start\', \'x\':\'0\'}}, \'NOTES : {1}\' ],\n'.format(''.join(indent_level), notes))
    #indent_level.pop()
    json_file.write('{0}],\n'.format(''.join(indent_level)))
    #indent_level.pop()
    json_file.write('{0}}},\n'.format(''.join(indent_level)))


# ------------------------------------------------------------------------------
# Add arrows:
# ------------------------------------------------------------------------------
def add_arrows(signal_array, json_file, indent_level, marked_edges, tex_blk, set_for_non_overlap_labels):


    logger.debug('+ {0}'.format(signal_array))
    #signal_array[0] = re.sub('^E:(.*)',r'\1', signal_array[0])
    decorations = []
    # Decode the style and type of arrow to be drawn. This is in signal_array 0
    decorations.append(re.sub('^[EL]:(.*)',r'\1', signal_array[0]))
    # the second column gives additional decoration but is not used currently.
    decorations = decorations + (signal_array[1].split(':'))
    for i in range(len(signal_array[2:])-1):
        if ((signal_array[i+3])):
            # Defines a baseline arrow style where the start point remains the same
            end = signal_array[i+3]
            if (re.search('^B', decorations[1])):
                start = signal_array[2]
            # Defines a chained arrow style where an arrow is drawn between successive pair of
            # points. 
            else:
                start = signal_array[i+2]

            # print a normal arrow with splines 
            if (re.search('[o\*]-[->\*o]?|[o\*->]-[o\*]', decorations[0])):
                start_level = marked_edges[' N('+start+')'][0]
                end_level = marked_edges[' N('+end+')'][1]
                # The waveform section has already been tex converted. So tex is
                # interpreted below. The fine tuning below is for proper arrow head
                # allignment, which also makes it unambiguous.
                if (re.search('\d+L',start_level)):
                    start_level = 'low'
                elif (re.search('\d+H',start_level)):
                    start_level = 'high'
                else:
                    start_level = 'MID'

                if (re.search('\d+L',end_level)):
                    end_level = 'low'
                elif (re.search('\d+H',end_level)):
                    end_level = 'high'
                else:
                    end_level = 'MID'
                # The special case where a Level is specified and the source and
                # destination are both in the same clock cycle.
                if (re.search('^L:',signal_array[0])):
                    column_start = re.sub('(^[A-Z]+).*',r'\1',start)
                    column_end = re.sub('(^[A-Z]+).*',r'\1',end)
                    if (column_start == column_end):
                        # For up arrows the destination is made to stop just
                        # outside the bsu boundary. Since this is a hardcoded
                        # offset, it will be messy for down arrow.  TODO:
                        # direction can be deciphered from TAG, since the excel
                        # column is captured. This cam be used for proper
                        # adjustment.
                        # tex_blk = tex_blk 
                        #           + '\draw [red,ultra thin, {0}]
                        #               ($({1}.center)-(0.5,0.25)$) --
                        #               ($({2}.center)-(0.5,0.6)$);\n'.format(decorations[0],
                        # start, end) 
                        tex_blk = draw_cycle_links(start,end,decorations[0],tex_blk)
                    
                else:
                    tex_blk = tex_blk + '\draw [red,ultra thin, {0}] ($({1}.{3})-(0.25,0)$)node[left=2pt]{{}} .. controls ++(6,0) and ++(-6,0) .. ({2}.{4}) node[above right=2pt] {{}};\n'.format(decorations[0], start, end, start_level, end_level) 

            # Add a measurement line from first point to next
            # for this special case the edge is point to point and will draw a
            # straight dimension line with dashed extensions.
            elif (re.search('|-|', decorations[0])):
                 if (re.search(r'\>' ,signal_array[4])):
                     logging.warning('\'{0}\' Expected a text label, found a marker instead' 
                                     .format(signal_array[4]))
                    
                 offset = 1; 
                 a  = re.sub('^[A-Z]+','',start)
                 b  = re.sub('^[A-Z]+','',end)
                 # To prevent crowding, we are forcing a vertical seperation between
                 # the labels, like drawing on a new line. the space is not created by
                 # default and it could thus overlap a drawn waveform. You may add an
                 # empty spacer line or empty signal if this is the case.
                 while ((a+str(offset) in set_for_non_overlap_labels) or (b+str(offset) in set_for_non_overlap_labels)):
                     offset += 1
                 
                 # For the time being, issue a warning, but in the future this can be
                 # fixed by adding a spacer in to the tex_blk
                 if (offset > 1):
                     logging.warning('Multiple dimensions drawn may overlap a waveform, Add a spacer in excel if required {0} {1}\n'.format(start,end))

                 set_for_non_overlap_labels.add(a+str(offset))
                 set_for_non_overlap_labels.add(b+str(offset))
                 tex_blk = tex_blk + draw_dimension_lines(start,end,signal_array[4], offset)
                 # allow only one edge to be drawn to prevent the name being interpreted as funny behaviour
                 break;

    return tex_blk 

# ------------------------------------------------------------------------------
# draw_same cycle_links
# ------------------------------------------------------------------------------
def draw_cycle_links(start,end,decoration,tex_blk):
    # Arrow South
    adjust_start = 0.25
    adjust_end = 0.55

    # Odd string compare behaviour.
    # so extract and convert to numbers
    a = re.sub(r'^[A-Z]+(\d+).*', r'\1', start)
    b = re.sub(r'^[A-Z]+(\d+).*', r'\1', end)
    

    # we can safely do this becasue all tags are structured and non repeating due
    # to them derived from excel unique cell names. 
    # Also we know the column is the same, so no need to split row and column
    # Sample and link signals.
    # Special case for sampling representaion, ie indicate a combinatorial
    # dependancy between two or more signals.
    if (re.search(r'[o\*]-[\*o]', decoration)):
        adjust_start = 0.25 
        adjust_end = -0.25 

    # Arrow south (swap)
    # Needed becasue of MID usage
    if (int(a) <  int(b)):
        adjust_end, adjust_start = -1*adjust_end, -1*adjust_start


    tex_blk = tex_blk + '\draw [red,ultra thin, {0}] ($({1}.MID)-(0.5,{3})$) -- ($({2}.MID)-(0.5,{4})$);\n'.format(decoration, start, end, adjust_start, adjust_end) 
    return tex_blk

# ------------------------------------------------------------------------------
# draw_edge_lines
# ------------------------------------------------------------------------------
def draw_edge_lines(signal_array, clock_edges, clk_filter, indent_level, marked_edges, tex_blk):
    """ Draw clock edge markers, according to the active edge of the clock"""

    logger.debug('+ Add clock cycle markers @ clock edge for {0}'.format(clk_filter))
    tex_blk = tex_blk + '\\begin{scope}[semitransparent,ultra thin]\n'
    tex_blk = tex_blk + '\\vertlines[gray]{{{0}}}\n'.format(','.join(str(i[1]) for i in clock_edges if (re.search(clk_filter, i[0]))))
    #%\vertlines[blue]{}
    tex_blk = tex_blk + '\end{scope}\n'
    cycle = ''
    for i in clock_edges:
        if (re.search(clk_filter, i[0])):
            #i[0] = re.sub('N\((-?\d+.*)\).*', r'\1',i[0])
            # FIXED: Issue 2:
            cycle = re.sub(r'N\(\S+?(-?\d+)\)', r'\1',i[0])
            i[0] = re.sub(r'N\((.*\d+.*)\)', r'\1',i[0])
            tex_blk = tex_blk + '\\draw ({0}.MID)node[above=6,right=-1pt]{{\\tiny {1}}};\n'.format(i[0], cycle) 

    return tex_blk

# ------------------------------------------------------------------------------
# draw_dimension_lines
# ------------------------------------------------------------------------------
# To indicate constraints or measurments three lines are drawn
# First, from the source clock to just below the destination signal, ie a
# veritical line
# Second, a similar line from the destination.
# Third, a horizontal dimension line from the end of first line to the
# destination
# and last, add the label from excel.
def draw_dimension_lines(start, end, t_label, offset):

    t_label = re.sub(r'_', r'\_', t_label)
    logger.debug('+ Add line with label {0}'.format(t_label))
    tex_blk = ''
    tex_blk = tex_blk + '\gettikzxy{{({0}.MID)}}{{\sx}}{{\sy}}\n'.format(start)
    tex_blk = tex_blk + '\gettikzxy{{({0}.MID)}}{{\ex}}{{\ey}}\n'.format(end)
    tex_blk = tex_blk + '\draw [red,ultra thin, densely dashed] ($(\\sx,\\sy)-(0,1)$) -- ($(\\sx,\\ey)-(0,{0})$);\n'.format(offset) 
    tex_blk = tex_blk + '\draw [red,ultra thin, |-|] ($(\\sx,\\ey)-(0,{2})$) -- ($(\\ex,\\ey)-(0,{1})$)node[ right=2pt] {{\\tiny {0}}};\n'.format(t_label, offset, offset) 
    return tex_blk

# ------------------------------------------------------------------------------
# To indicate some kind of zero cycle effect, we offset the signal by a small
# amount. Keep this controllable so that it can be used for some relative
# timeing as will in the future.
# ------------------------------------------------------------------------------
def time_offset_signal(signal_array, scale):
    pass
    #offset = re.sub(r'.*<(.0.\d+)>.*', r'\1',signal_array[0]) 
    #offset = float(offset)*scale
    #print (float(offset)*scale)
    #signal_array[1] = re.sub(r'(.*)^\d+(.*)',r'\1offset\2' , signal_array[1])
    #taps = [i for i, step in enumerate(signal_array) if re.search(r'dotted',step)]
    #print(taps)
    #print(('WARN  : Adding offse to signal, Is it really required...?' ))


# ------------------------------------------------------------------------------
# 
# ------------------------------------------------------------------------------
def sanitize(text):
    """Replace or escape special chars to prevent tex errors"""
    #text = re.sub(r'[*]',r'\*',text) 
    text = re.sub(r'~',r'\~',text) 
    #text = re.sub(r'<',r'\textless',text) 
    #text = re.sub(r'>',r'\textgreater',text) 
    text = re.sub(r'\|',r'\|',text) 
    text = re.sub(r'_',r'\\_',text) 
    return text

def check_spacers(raw_signal_array, set_of_spacer_marks):
    """Build an image of spacer marks while scanning top to bottom

       The assumption is that the top row will always contain the required
       spacer. The entire column must contain spacers but it is easy to make
       the mistake of not including a spacer in a later row. Force a spacer and
       emit a wanring so reduce design cycles due to misalignment
    """
                       
    temp =[i for i, state in enumerate(raw_signal_array)
            if re.search('^\|$', state)]
    # Build the set of spacers for uniformity in rendering.
    # if a space is missedin Excel, it will be forced on
    # the wave.
    if any((set_of_spacer_marks - set(temp))):
        logging.warning('{1} Possible missing spacers, Wave will be overwritten with spacers at columns-{0}'.format(sorted(set_of_spacer_marks), raw_signal_array[0]))
    set_of_spacer_marks = set_of_spacer_marks | set(temp)
    return set_of_spacer_marks

def sanitize_spacers(raw_signal_array, set_of_spacer_marks):
    """Force spacer marks on raw signal, ie from CSV such that the redering
    would be correct and alligned. A warning would have been issued in the
    check phase
    """
    # Force spacer marks
    for spacer_index in set_of_spacer_marks:
        raw_signal_array[spacer_index] = '|';
    return raw_signal_array

def main():
# ------------------------------------------------------------------------------
# Main
# The tex is based on the following references.
# tikz-timing-> this is where the timing fonts and the meat of the timing
# diagram capability is
# tikzpgf->     this is used for grahic overlays and annotation
# ------------------------------------------------------------------------------

    timing_block = [];
    tex_blk_notes = ''
    tex_blk_note_labels = ''
    tex_blk_drawedges = ''
    clock_edges = []
    # Scale will stretch the waveform horizontally.
    # changing the scale will also have an impact on how many characters can fit
    # comfortably within a bus
    scale  = 4 
    note_label_count = 0
    set_for_non_overlap_labels = set();
    set_of_spacer_marks = set()
    if (len(sys.argv) == 4):
        in_file = sys.argv[1]
        out_file = sys.argv[2]
        scale  = int(sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
    indent_level =[]
    wave_section = 1 
    
    # this is a standard tex header to pull in all packages that are necessary.
    tex_block=r'''
    \documentclass[landscape,draft]{report}
    %\usepackage{tikz-timing}[2017/12/10]
    \usepackage{tikz-timing}[2011/01/09]
    \usepackage{hyperref}
    % This does not work, Need some debug
    \hypersetup{pdfauthor={AVN},%
                pdftitle={PDF meta information},%
                pdfsubject={Sample document with blind text},%
                pdfkeywords={hyperref, PDF meta information},%
                pdfproducer=TeXShop,%
                pdfcreator=pdflatex}
    
    %\usepackage{showframe}
    
    \usepackage{courier}
    %\renewcommand{\ttdefault}{courier}
    \usepackage[T1]{fontenc}
    
    %\usetikztiminglibrary[simple]{advnodes}
    \usetikztiminglibrary{advnodes}
    \usetikzlibrary{arrows.meta}
    \pagestyle{empty}
    \def\degr{${}^\circ$}
    \usetikzlibrary{arrows}
    \usetikzlibrary{shapes}
    \usepackage[text={26cm,19cm},centering]{geometry}
    \pgfsetroundcap
    \pgfdeclarelayer{background}
    \pgfdeclarelayer{annotations}
    \pgfsetlayers{background,main,annotations}
    \tikzset{timing/table/.append style={font=\ttfamily\scriptsize}}
    %\tikzset{timing/font/.cd/.append style={font=\ttfamily\scriptsize}
    %\tikzset{timing/d/text/.append style={font=\sffamily\scriptsize}}
    \tikzset{timing/d/text/.append style={font=\ttfamily\scriptsize}}
    
    %Use this package for notes enumeration
    \usepackage{enumitem}
    \setlist[enumerate]{font=\sffamily\scriptsize, topsep=0pt,itemsep=-1ex,partopsep=1ex,parsep=1ex}
    \newlist{deflist}{description}{1}
    \setlist[deflist]{labelwidth=2cm,leftmargin=!,font=\normalfont}
    
    \makeatletter
    \newcommand{\gettikzxy}[3]{%
        \tikz@scan@one@point\pgfutil@firstofone#1\relax
        \edef#2{\the\pgf@x}%
        \edef#3{\the\pgf@y}%
    }
    \makeatother
    
    \begin{document}
    \begin{tikztimingtable}[>=angle 90, timing/picture, timing/nodes/.cd,advanced,]
    '''
    with open(in_file , 'r') as csv_file:
        with open(out_file, 'w') as json_file:
            json_file.write(tex_block)
            #indent_level.append('  ')
            for i, line in enumerate(csv_file):
                
                logger.debug('Processing csv file @ line {0}'.format(i)) 
                logger.debug('   line {0}'.format(line)) 
    
                line=line.strip()
                line=line.rstrip('\r\n')
                # Although we read in a CSV we are using ; as a delimiter. The
                # reason for doing so is to preserve ',' which we tend to use a lot
                # in text
                signal_array = line.split(';')
                signal_array[0] = re.sub('_','\_',signal_array[0]);
                end = len(signal_array)
                if (re.search('TITLE', signal_array[0])):
                    title = ''.join(signal_array[1:])
                elif (re.search(':SCALE:',signal_array[0])):
                    # Overwrite what is coming from the command line.
                    # this allows specific control per worksheet in batch mode.
                    scale = int(signal_array[1])

                    # Embed :END: on any column in the row of :SCALE:
                    # stop rendering waveform beyond the column.
                    # The default method is to look for empty cells, which is
                    # partially encoded in the number of csv fields writterout
                    # but the csvwriter method. But this it not very reliable.
                    # Hence the inclusion of :END: as a reliable method.
                    if ':END:' in signal_array:
                       end =signal_array.index(':END:') 
                       logging.info('Found END at column {0}, Will only draw till End.'.format(end))
                    else:
                       end = len(signal_array)
                       logging.warning('No :END: found , Draw waves till first empty column cell ({0} )in clock row.'.format(end))
                elif (re.search('NOTE:', signal_array[0])):
                    # Reached the end of the signal block as per the structure of
                    # Excel 
                    if (re.search(':NOTE:', signal_array[0])):
                        marked_edges = dump_timingtable(
                                           timing_block,
                                           json_file,
                                           indent_level) 
                        # Switched of waveform capture
                        wave_section=0
                        continue
                    # skip empty cells
                    # The assumption is notes section has 2 columns, 
                    notes = ''.join(signal_array[2:])
                    signal_array = filter(None, signal_array)
    
                    # skip if notes are empty
                    if (len(signal_array) > 1):
                        # A value of zero obviosly means that the node which was
                        # originally there has been moved.
                        if (signal_array[1] == '0'):
                            raise ValueError('Unexpected node label for notes') 
                        #indent_level.append('  ')
                        # Section to add labels at the marked edges
                        # notes section with actual text, the notes are numbered
                        # from top to bottom as they appear in the Excel. But for
                        # readability, ie (to locate the corresponding mark) the
                        # order should be like a raster scan (left to rt, top to
                        # bottom). Leave the reordering to user for the time being.
                        # FIXME this is an afterthought, like many other things here
                        # Look for a labelled node of the form AB9> in an excel
                        # cell
                        elif (re.search(r'^[A-Z]+\d+>', signal_array[1])):
                            note_label_count += 1
                            tex_blk_note_labels = tex_blk_note_labels + '\\draw [gray, ultra thin, {{Circle[length=1pt]}}-] ($({0}.HIGH)-(0.5,0.07)$) node[above=3,left=-1pt] {{\\tiny \\em {1}}} -- ($({0}.HIGH) +(-0.5,0.6)$);\n' .format(signal_array[1], note_label_count) 
    
                            temp = ('{0}\item ({2}) {1}\n' .format(''.join(indent_level), notes, note_label_count))
                        else:
                            # If NOTE: appears w/o a proper marker, then it is
                            # assumed to be a continuation of previous NOTE. but
                            # printed as a new para. Strip of the leading ` as this
                            # will be used to prevent XL complaingin about use of
                            # operators.
                            notes = re.sub(r'\`', '',notes)
                            temp = ('\subitem{0}\\hspace{{1em}}{1}\n'.format(''.join(indent_level), notes))
    
                        tex_blk_notes = tex_blk_notes + sanitize(temp)
    
                        #indent_level.pop()
    
                # draw an arrow from edge or level    
                elif (re.search('^E:|^L:', signal_array[0])):
                    #indent_level.append('  ')
                    # the arrows are processes and drawn as and when they are
                    # endountered in the CSV. This is in the :ANNOTATE: Section.
                    # but the section check is never done.
                    tex_blk_drawedges = add_arrows(signal_array, json_file, indent_level, marked_edges, tex_blk_drawedges, set_for_non_overlap_labels)
                # draw clock markers.
                elif (re.search('^D:\|\|', signal_array[0])):
                    # the clock marks appear under the Section :CLK_MARKS: but this
                    # check is not performed.
                    clk_filter = '*'
                    # Cxx: is used for the search. so if it is missing from clock
                    # perhaps we should flag an error upfront.
                    if re.search('C\d+:',signal_array[2]):
                        clk_filter = re.sub(r'C\d+:(.*)', r'\1', signal_array[2])
                        clk_filter = re.sub(r'_', '', clk_filter)
                        logger.debug('{0}'.format(clk_filter))
    
                    tex_blk_drawedges = draw_edge_lines(signal_array, clock_edges,clk_filter, indent_level, marked_edges, tex_blk_drawedges)
                elif (wave_section):
                    # Issue 4:
                    # process only till end marker for the wave section.
                    signal_array = signal_array[0:end+1]
                    # Once the wave_section is dumbped, ie when :NOTES: is
                    # encountered in source, dsiable furhter signals from being
                    # recognised.
                    if (re.search('^G:', signal_array[0])):
                        add_grp(signal_array, json_file, indent_level, scale)
                        # Add a spacer row above a group for readability
                        timing_block.append('' * len(signal_array))
                        timing_block.append(signal_array)
                    elif (re.search('^B:|^b:', signal_array[0])):
                        set_of_spacer_marks = check_spacers(signal_array, set_of_spacer_marks)
                        signal_array = sanitize_spacers(signal_array, set_of_spacer_marks)
                        add_bus(signal_array, json_file, indent_level, scale)
                        timing_block.append(signal_array)
                    elif (re.search('^M:', signal_array[0])):
                        add_marker(signal_array, json_file, indent_level, scale)
                        timing_block.append(signal_array)
                    elif (re.search(r'(?i)^C\d+:', signal_array[0])):
                        set_of_spacer_marks = check_spacers(signal_array, set_of_spacer_marks)
                        signal_array = sanitize_spacers(signal_array, set_of_spacer_marks)
                        add_clock(signal_array,json_file, indent_level, scale, clock_edges)
                        timing_block.append(signal_array)
                    elif (re.search('\S+', signal_array[0])):
                        set_of_spacer_marks = check_spacers(signal_array, set_of_spacer_marks)
                        signal_array = sanitize_spacers(signal_array, set_of_spacer_marks)
                        add_signal(signal_array,json_file, indent_level, scale)
                        timing_block.append(signal_array)
                    else:
                        #json_file.write('{0}\\\\\n'.format(''.join(indent_level)))
                        timing_block.append('\\' )
                    # Here we handling the decoration of signal name, namely italics and
                    # bold  
                    signal_array[0] = re.sub(r'(.*)<i>',r'\\textit{\1}', signal_array[0]) 
                    signal_array[0] = re.sub(r'(.*)<b>',r'\\textbf{\1}', signal_array[0]) 
                    signal_array[0] = re.sub(r'(.*)<u>',r'\\underline{\1}', signal_array[0]) 
                    if (re.search(r'<.0.\d+>', signal_array[0])):
                        # Undo the last signal push, The signal is still in signal_array.
                        timing_block.pop()
                        time_offset_signal(signal_array, scale)
                        timing_block.append(signal_array)
    
    
            # add the title grabbed from CSV
            
            # add the NOTES grabbed from CSV
    
            # construct tex document
            tex_blk_extracode_pgfopen = ''; 
            tex_blk_extracode_pgfopen = tex_blk_extracode_pgfopen + ('{0}\extracode\n'.format(''.join(indent_level)))
            tex_blk_extracode_pgfopen = tex_blk_extracode_pgfopen + ('{0}\\tablerules\n'.format(''.join(indent_level)))
            tex_blk_extracode_pgfopen = tex_blk_extracode_pgfopen + ('{0}\\begin{{pgfonlayer}}{{annotations}}\n'.format(''.join(indent_level)))
            #indent_level.append('  ')
            tex_blk_extracode_pgfopen = tex_blk_extracode_pgfopen + ('{0}\\tableheader{{}}{{{1}}}\n'.format(''.join(indent_level), title))
    
            #indent_level.append('  ')
            json_file.write(tex_blk_extracode_pgfopen)
            #tex_blk_drawedges = re.sub(r'\\draw', ''.join(indent_level)+r'\\draw', tex_blk_drawedges)
            json_file.write(tex_blk_drawedges)
            json_file.write(tex_blk_note_labels)
    
            tex_blk_close_pgf_tikz = ('{0}\end{{pgfonlayer}}\n'.format(''.join(indent_level)))
    
            tex_blk_close_pgf_tikz = tex_blk_close_pgf_tikz + ('{0}\end{{tikztimingtable}}\n'.format(''.join(indent_level)))
    
            json_file.write(tex_blk_close_pgf_tikz)
    
            #if (re.search('.',tex_blk_notes)):
            # always print the header
            json_file.write('\\par {\\ttfamily\scriptsize{NOTE:}\n')
            if (tex_blk_notes):
                json_file.write('{0}\\begin{{enumerate}}{{}}\n'.format(''.join(indent_level)))
                #indent_level.append('  ')
    
                json_file.write('{0}\\setlength{{\\leftskip}}{{2.3cm}}\n'.format(''.join(indent_level)))
                json_file.write('{0}\\ttfamily\\scriptsize\n'.format(''.join(indent_level)))
                #indent_level.pop()
    
                json_file.write(tex_blk_notes)
                #indent_level.pop()
    
                json_file.write('{0}\end{{enumerate}}\n'.format(''.join(indent_level)))
    
            json_file.write('}}{0}\end{{document}}\n'.format(''.join(indent_level)))
    

if __name__=="__main__":
    logger.info('{0}'.format(__name__))
    main()
#-------------------------------------------------------------------------------
# Fixed bugs
#-------------------------------------------------------------------------------
#Issue 1: 
# A break followed by a data tag which has a 'S' (capital) screws up the
# waveform from that point. This is mostly attributed to the greedy matching
# usded to figure out an S. A temporary solution is to search for 'S' with word
# breaks to identify such occurances.
#Issue 2:
#  Negative cycle numbers while legitimate were not being rendered properly.        
#Issue 3:
# Added a mechanism to control scale from CSV. This makes the intent clear and
# mixing of sheets for batch processing.
#Issue 4:
#Added a mechanism to control right bound for drawn columns.
#Issue 5:
# Sapacer need to be uniform. Testing and automating this helps reduce design
# cycles. Implmented methods check_spacers and sanitize_spacers.
