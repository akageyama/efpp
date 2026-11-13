# efpp
efpp: A preprocessor for eFortran, a dialect of the modern Fortran

## Usage

An eFortran source file has the extension `.ef`. The `efpp.py` preprocessor converts it into a standard Fortran source file with the extension `.F90`.

For example:

```bash
./efpp.py sample.ef > sample.F90
```

The generated `sample.F90` can be compiled with a standard Fortran compiler, such as `gfortran`.

### Using efpp with Make

For projects using GNU Make, the following rule converts `.ef` files into `.F90` files:

```makefile
EFPP = ../efpp.py

%.F90: %.ef
	@rm -f $@.tmp
	@$(EFPP) $< > $@.tmp || { rm -f $@.tmp; exit 1; }
	@mv -f $@.tmp $@
```

The preprocessor first writes to a temporary file. Only after successful conversion is the temporary file renamed to the target `.F90` file.

If preprocessing fails, the temporary file is removed and any existing `.F90` file is preserved.

The path to `efpp.py` should be adjusted to match the project directory structure. The command lines in the Makefile rule must begin with a TAB character.

A working example is provided in [`sample_code/Makefile`](sample_code/Makefile).


## Functions


### Member access with `.`

In eFortran, a dot (`.`) can be used instead of the standard Fortran component selector `%` for derived types:

```fortran
call field.advance(time.dt)
```

This becomes:

```fortran
call field%advance(time%dt)
```

Numeric decimal points, quoted strings, comments, and recognized dot operators (such as `.and.`) are not converted. In ordinary expressions, write user-defined dot operators with spaces, as in `a .cross. b`, to distinguish them from component access.

### Shorter declarations

The following eFortran annotations are expanded into standard Fortran declaration attributes:

| eFortran annotation | Fortran attribute(s) |
| --- | --- |
| `<in>` | `intent(in)` |
| `<out>` | `intent(out)` |
| `<io>` | `intent(inout)` |
| `<optin>` | `intent(in), optional` |
| `<optout>` | `intent(out), optional` |
| `<optio>` | `intent(inout), optional` |
| `<const>` | `parameter` |

For example:

```fortran
integer(SI) <in> :: i, j, k
real(DR) <optin> :: pi
```

The current implementation performs text substitutions for these annotations and expects spaces around the annotation tokens.

### "Just once" block

A `just_once` block is executed while the logical variable `just_once` is true. Its closing marker sets that variable to false.

```fortran
program test
  implicit none
  logical :: just_once = .true.

  ==<just_once>==
    print *, "Executed only once"
  ==</just_once>==
end program test
```

The program must declare and initialize `just_once` itself. The preprocessor translates the opening and closing markers to an `if (just_once) then` block and `just_once = .false. ; end if`, respectively.

### "Skip" block

A `skip` block executes its body when `mod(counter, interval) == 0`, and increments the named counter at the closing marker.

```fortran
program test
  implicit none
  integer :: ctr = 0, i

  do i = 1, 200
    ===<skip ctr:8>===
      print *, i
    ===</skip ctr>===
  end do
end program test
```

In this example, the body runs when `ctr` is a multiple of 8. The counter must be declared and initialized by the program.

### Predefined macros

The preprocessor recognizes the following source-location and routine-name macros:

| Macro | Replacement |
| --- | --- |
| `__MODULE__` | Outermost recognized program or module name |
| `__FUNC__` | Recognized subprogram name (or nested subprogram path) |
| `__MODFUNC__` | Program/module name followed by subprogram path |
| `__LINE__` | Source line number |
| `__MODLINE__` | Program/module name followed by the source line number in parentheses |

These replacements can also be used inside string literals. Name-based macros depend on the program and subprogram declarations recognized by the current lightweight parser.

### User-defined aliases

User-defined text substitutions are specified in `efpp_alias.list` (or in an alias file passed as the second command-line argument):

```text
"do i bulk" => "do i = 1, NXPP"
"__EFPPVER__" => "180802"
```

A definition can also span multiple lines, as described by the examples in `efpp.py`. The replacement is textual and follows definition order; replacement text may itself match a later alias. Duplicate aliases, unrecognized definition syntax, and incomplete definitions at the end of the file are reported as errors.

### `implicit none` check

The preprocessor performs a simple check for `implicit none` near the beginning of a recognized `program` or `module`. This is not a full Fortran syntax check and does not independently validate every program unit.

### Compound assignment operators

The preprocessor expands `+=`, `-=`, and `*=` into ordinary Fortran assignments:

```fortran
x += y                 ! x = x + y
x -= y                 ! x = x - y
x *= 2                 ! x = x * 2
if (x > 0) a(i) += b   ! if (x > 0) a(i) = a(i) + b
```

It also supports component and array references (including spaces inside subscripts) and multiple statements separated by semicolons. Text inside strings and comments is preserved.

The Fortran inequality operator `/=` is **not** treated as a compound assignment. Because a compound assignment duplicates the left-hand side in the generated code, avoid side-effecting expressions such as `a(next_index()) += 1`.

### Block comments

eFortran supports block comments delimited by `!!>` and `!!<`.

For example:

```fortran
program test
  implicit none

  print *, "Before"

  !!>
  print *, "This line is commented out."
  print *, "This line is also commented out."
  !!<

  print *, "After"
end program test
```

The preprocessor comments out lines between `!!>` and `!!<` by inserting `!` at the beginning of each line.

Block comments can also be nested. Each additional nesting level adds another `!` to the beginning of the affected lines.

The original number of lines is preserved, so source line numbers remain unchanged.

### Subsidiary call

```
       xyz -call abc()  =>  xyz ;call abc()
           -call abc()  =>       call abc()
```

This could be convenient for test or timer routine calls.


## Using Vim quickfix with eFortran

When efpp converts an `.ef` file to `.F90`, it preserves the number and order of source lines. This makes it possible to use Vim's quickfix feature to jump from compiler diagnostics for generated `.F90` files to the corresponding `.ef` source lines.

For example, suppose `sample.F90` was generated from `sample.ef`. After compiling with `:make`, the quickfix list may contain references to `sample.F90`. Those filenames can be changed to `sample.ef` without changing the line numbers.

The following optional mapping can be added to your `.vimrc`:

```vim
nnoremap <silent> Y :copen<CR>:setlocal modifiable<CR>:%s/\.F90\>/.ef/g<CR>:call histdel('/', -1)<CR>:cbuffer<CR>:cclose<CR>
```

Use it as follows:

1. Run `:make` in Vim to compile the program and populate the quickfix list.
2. If the list contains compiler errors referring to generated `.F90` files, press `Y` to replace those filename extensions with `.ef`.
3. Use `:cnext`, `:cprev`, or `:copen` to navigate the errors in the original eFortran files.

The pattern `\.F90\>` matches a literal `.F90` extension rather than an arbitrary character followed by `F90`. This mapping assumes that `.F90` filenames in the quickfix list correspond to `.ef` source files with the same base names. It is not a general-purpose source-map mechanism, and it does not address transformations that change the line numbering.

**Note:** This mapping overrides Vim's normal-mode `Y` command. Choose a different key if you already use `Y` for another purpose.

## Reference

S. Hosoyamada and A. Kageyama, "A Dialect of Modern Fortran for Simulations" in Methods and Applications for Modeling and Simulation of Complex Systems, Communications in Computer and Information Science, vol 946, pages 439-448, 2018 (Proceedings of AsiaSim2018)
