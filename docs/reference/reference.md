# Reference Manual
The API of Tabbed consist of 4 components that work together to read a delimited
text file. The `reading`,`sniffing`,`tabbing`, and `parsing` modules contain
these components. A reader instance from the `reading' module can modify and
call all of these components, making the reader the main interface for users.
However, developers looking to extend Tabbed will need to know how each
component works.  The source code documentation is here.

<div class="grid cards" markdown>
- ## :material-read: [reading](reading.md)
- ## :material-file-find-outline: [sniffing](sniffing.md)
- ## :material-file-table: [tabbing](#)
- ## :material-rename: [parsing](#)
</div>


