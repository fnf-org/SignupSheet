from __future__ import print_function 

from datetime import datetime, timedelta, timezone
import re
import urllib.parse

from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
from antlr4.error.Errors import ParseCancellationException, InputMismatchException

from signup.models import Coordinator, Job
from signup.parser.StaffSheetLexer import StaffSheetLexer
from signup.parser.StaffSheetListener import StaffSheetListener
from signup.parser.StaffSheetParser import StaffSheetParser
    
import signup.gql_wrapper as gql 

class SchemaBuilder(StaffSheetListener) :
    
    #epoch = datetime.strptime('07/27/2016 00:00:00 UTC', '%m/%d/%Y %H:%M:%S %Z')
    epoch = datetime.now(timezone.utc)

    def __init__(self, user, source=None):
        self.rows = []
        self.stack = []
        self.context = []
        self.user = user
        if source is not None :
            self.context.append(source)

    def enterRole(self, ctx):
        title = urllib.parse.quote(self.__strToken(ctx.QUOTE()), safe=' ')
        
        inputstream = ctx.start.getInputStream()
        start = ctx.getChild(3).start.start
        stop = ctx.getChild(3).stop.stop
        text = inputstream.getText(start, stop)
        
        # Returns the source ID

        src = gql.create_source(gql.Source(
            id=None,
            title=title,
            text=text,
            owner=self.user.first_name + ' ' + self.user.last_name,
            version=datetime.now(timezone.utc).isoformat('T'),
        ))

        self.context.append(src)

    def exitRole(self, ctx):
        self.context.pop()
        
    def exitRolefragment(self, ctx):
        source = self.context[-1]
        description = self.stack.pop()
        contact = self.stack.pop()
        status = self.stack.pop()
        if status == 'active' :
            status = "ACTIVE"
        elif status == 'disabled' :
            status = "DISABLED"
        else :
            status = "WORKING"

        role = gql.Role(
            id=None,
            status=status,
            source=source,
            contact=contact,
        )
        gql.create_role(role)

        # Now that the role exists, we can create the other rows
        # which have FK constraints 
        for row in self.rows:
            gql.create_job(row)

        self.rows = []

    def exitStatus(self, ctx):
        self.stack.append(ctx.getChild(1).getText())

    def exitCoordinator(self, ctx):
        pass
        #coord = Coordinator()
        #coord.source = self.context[-1]
        #coord.name = self.__strToken(ctx.QUOTE(0))
        #coord.email = self.__strToken(ctx.QUOTE(1))
        #coord.url = self.__strToken(ctx.QUOTE(2))
        ### XXX: Coordinators not loading. 
        #self.rows.append(coord)

    def exitContact(self, ctx):
        self.stack.append(self.__strToken(ctx.QUOTE()))

    def exitDescription(self, ctx):
        self.stack.append(self.__strToken(ctx.QUOTE()))
        
    def exitJob(self, ctx):
        for slot in self.stack.pop():
            source = self.context[-1]
            title = self.__strToken(ctx.QUOTE(0))
            description = self.__strToken(ctx.QUOTE(1))
            start = slot['begin']
            end = slot['end']
            needs = 1            
            if ctx.needs() != None :
                needs = self.__intToken(ctx.needs().NUMBER())
            protected = ctx.getChild(0).getText() == 'protected'

            job = gql.Job(
                id=None, 
                source=source, 
                title=title, 
                start=start, 
                end=end, 
                description=description, 
                needs=needs, 
                protected=protected)

            self.rows.append(job)
                           
    def exitTimespec(self, ctx):
        times = [self.__timespecToken(x) for x in ctx.getTokens(StaffSheetLexer.TIME)]
        numbers = [int(x.getText()) for x in ctx.getTokens(StaffSheetLexer.NUMBER)]
        duration = self.stack.pop()
        slots = []
        if len(times) == 1 and len(numbers) == 1 : 
            # This is a count job
            for i in range(numbers[0]) :
                slot = {}
                slot['begin'] = times[0] + (duration * i)
                slot['end'] = slot['begin'] + duration
                slots.append(slot)
        elif len(times) == 2 :
            # This is an until job
            cursor = times[0]
            until = times[1]
            while cursor < until : 
                slot = {}
                slot['begin'] = cursor
                cursor += duration
                slot['end'] = cursor
                slots.append(slot)
        else:         
            slot = {}
            slot['begin'] = times[0]
            slot['end'] = slot['begin'] + duration
            slots.append(slot)

        self.stack.append(slots)

    def exitDuration(self, ctx):
        value = float(ctx.getToken(StaffSheetLexer.NUMBER, 0).getText())
        magnitude = ctx.getChild(2).getText()
        if magnitude[0:4] == 'hour' :
            self.stack.append(timedelta(hours=value))
        else:
            self.stack.append(timedelta(minutes=value))
        
    def __strToken(self, token) :
        if token is None:
            return ""
        
        s = token.getText();
        # Stip quotes 
        s = s[1:-1]
        # Trim 
        s = s.strip()
        return s
    
    def __intToken(self, token) :
        return int(token.getText())

    def __floatToken(self, token) :
        return float(token.getText())

    def __timespecToken(self, token):
        spec = token.getText()
        (day, time) = spec.split()
        d = 0
        h = 0
        m = 0
        if day[1:] == 'riday' :
            d = 2
        elif day[1:] == 'aturday' :
            d = 3
        elif day[1:] == 'unday' :
            d = 4
        elif day[1:] == 'onday' :
            d = 5
        elif day[1:] == 'uesday' :
            d = 6
        elif day[1:] == 'ednesday' :
            d = 0
        elif day[1:] == 'hursday' :
            d = 1
        else :
            raise ValueError("This date is fucked: " + spec)

        if time[1:] == 'idnight' :
            h = 0
        elif time[1:] == 'oon' :
            h = 12
        else :  
            regex = re.compile("(\d+):(\d+)\s*(am|pm)")
            matcher = regex.search(time)
            h = int(matcher.group(1)) % 12
            if matcher.group(3) == 'pm' :
                h += 12
            m = int(matcher.group(2))
        
        realtime = self.epoch + timedelta(days=d, minutes=m, hours=h)
        return realtime   

class ReportedException(ParseCancellationException) :
    def __init__(self, s, l) :
        self.symbol = s
        self.line = l 
        self.message = "Parse error on line " + str(self.line) + "."
        if s is not None :
            self.message = self.message + " Something went wrong around \"" + self.symbol.text + "\""
        
    def __str__(self):
        return "message " + self.message
        
class ValidateErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise ReportedException(offendingSymbol, line)

class ValidationErrorStrategy(DefaultErrorStrategy):
    def recover(self, recognizer, e):        
        context = recognizer._ctx
        raise ReportedException(context.start, context.start.line)

    def recoverInline(self, recognizer):
        self.recover(recognizer, InputMismatchException(recognizer))

    def sync(self, recognizer):
        pass


def __setup_parser(parse_input):
    strat = ValidationErrorStrategy()
    errs = ValidateErrorListener()

    lexer = StaffSheetLexer(parse_input)
    stream = CommonTokenStream(lexer)
    parser = StaffSheetParser(stream)
    
    parser._errHandler = strat
    parser.addErrorListener(errs)
    lexer.addErrorListener(errs)

    return parser
    
def build(user, sourceobj=None, sourcetext=None, test_parse=False):
    
    if sourceobj is not None :
        stream = InputStream(sourceobj.text)
    elif sourcetext is not None : 
        stream = InputStream(sourcetext)
    else :
        raise ValueError("sourceobj or sourcetext must not be None")
    
    parser = __setup_parser(stream)
    tree = parser.rolefragment()

    if not test_parse :
        builder = SchemaBuilder(user=user, source=sourceobj)
        ParseTreeWalker.DEFAULT.walk(builder, tree)

def build_all(text, user=None, test_parse=False):

    stream = InputStream(text)
    parser = __setup_parser(stream)
    tree = parser.sheet()

    if not test_parse :
        builder = SchemaBuilder(user)
        ParseTreeWalker.DEFAULT.walk(builder, tree)
