# eFortran / efpp

**A lightweight, readability-oriented dialect of Modern Fortran for scientific simulation codes.**

[eFortran](https://github.com/akageyama/efpp) adds a small set of conveniences to ordinary Fortran: dot notation for derived-type components, compound assignments, shorter declaration attributes, and a few useful block constructs. **efpp** is a Python preprocessor that translates an eFortran source file (`.ef`) into standard Fortran source (`.F90`). The resulting file is compiled by your usual Fortran compiler.

eFortran is **not a new compiler**. It is a thin preprocessing layer intended for scientific and numerical software, where readable source code and compatibility with existing Fortran tools are important. In particular, efpp aims to keep source line numbers aligned between `.ef` and `.F90` files, making compiler diagnostics easier to trace.

## At a glance

| eFortran | Generated Fortran | Purpose |
| --- | --- | --- |
| `call field.advance(time.dt)` | `call field%advance(time%dt)` | Component access with `.` |
| `x += dx` | `x = x + dx` | Compound assignment |
| `!debugp i` | `print *, 'i = ', i` | Print a labeled value with source location |
| `real(DR) <in> :: dt` | `real(DR), intent(in) :: dt` | Short declaration attributes |
| `if <just_once>` | `if (just_once) then` | One-time block (with a closing action) |
| `if <skip counter:8>` | `if (mod(counter,8)==0) then` | Execute every eighth encounter (with a closing action) |

The `!debugp` translation shown above is schematic: efpp also includes the source location in the generated output. The last two rows show **opening lines only**. Their closing `end if` lines also generate code, as explained below.

## Getting started

### Requirements

- **Python 3** to run `efpp.py` (no third-party Python packages are required by the script).
- A **Fortran compiler**, such as `gfortran`, to compile the generated `.F90` files.
- **GNU Make** only if you want to use the included Makefile-based example.

Clone the repository:

```sh
git clone https://github.com/akageyama/efpp.git
cd efpp
```

Try the included sample program:

```sh
cd sample_code
make
```

The sample Makefile converts the `.ef` files, compiles them with `gfortran`, and runs the resulting program. Its conversion rule preserves an existing `.F90` file if preprocessing fails.

### A small example

Save the following as `demo.ef` in a working directory:

```fortran
program demo
  implicit none
  type :: simulation_state
    integer :: step = 0
    real :: energy = 1.0
  end type simulation_state
  type(simulation_state) :: state
  logical :: just_once = .true.
  integer :: i

  do i = 1, 5
    if <just_once>
      print *, "Starting simulation"
    end if
    state.step += 1
    state.energy *= 0.5
  end do

  !debugp state.step, state.energy
end program demo
```

From that working directory, run efpp (adjust the path to `efpp.py` to match your installation):

```sh
python3 /path/to/efpp/efpp.py demo.ef > demo.F90
gfortran -o demo demo.F90
./demo
```

The program prints `Starting simulation` once, then updates the components of `state` using dot notation and compound assignments. The `!debugp` statement displays `state.step = 5` and `state.energy = 0.03125`, together with the program name and source line number. efpp converts component access (`.`) to standard Fortran (`%`).

**No alias file is required for this example.** If `efpp_alias.list` exists in the current working directory, efpp loads it automatically; otherwise, it uses its built-in substitutions alone.

## Language features

### Dot notation for components

Use `.` instead of `%` when accessing derived-type components:

```fortran
call field.advance(time.dt)
a(i).value += dt
```

This is converted to:

```fortran
call field%advance(time%dt)
a(i)%value = a(i)%value + dt
```

Decimal points, quoted strings, comments, intrinsic dot operators (such as `.and.`), and recognized user-defined operators are protected. In ordinary expressions, **surround user-defined dot operators with spaces**, for example `a .cross. b`, to avoid ambiguity with member access. This is a lightweight transformation, not full Fortran parsing.

### Shorter declarations

| eFortran | Fortran declaration attribute(s) |
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
real(DR) <in> :: dt
integer <optout> :: status
```

These annotations are implemented as text substitutions; **include spaces around the tokens** as shown.

### Compound assignments

`+=`, `-=`, and `*=` expand into standard assignments:

```fortran
x += dt
energy -= loss
a(i) *= factor
if (x > 0) a(i) += b
```

The preprocessor also supports array subscripts containing spaces and multiple semicolon-separated statements on one line. It does **not** reinterpret Fortran's `/=` inequality operator.

Because the left-hand side is duplicated in the generated code, avoid expressions with side effects on the left, such as `a(next_index()) += 1`: the function could be evaluated twice.

### One-time blocks: `just_once`

The recommended syntax is:

```fortran
logical :: just_once = .true.

if <just_once>
  call initialize()
end if
```

The block is converted to an ordinary `if (just_once) then` block. Its closing line sets `just_once = .false.` before ending the conditional. **You must declare and initialize the logical variable `just_once` yourself.** Once the block has executed, subsequent encounters skip its body unless your program sets the variable to true again.

For compatibility, the original syntax is also supported:

```fortran
==<just_once>==
  call initialize()
==</just_once>==
```

Both forms retain line-number correspondence. Nested `just_once` blocks are not allowed; the unified block parser checks this and reports mismatched markers.

### Periodic blocks: `skip`

The recommended syntax is:

```fortran
integer :: counter = 0

if <skip counter:8>
  call write_output()
end if
```

This is equivalent to:

```fortran
if (mod(counter,8)==0) then
  call write_output()
end if; counter = counter + 1
```

The body executes when the counter is divisible by 8. **The counter is declared and initialized by your program**, not by efpp. The counter increments at the end of the block, whether or not the body executed. The starting value therefore matters: starting at 0 executes the body on the first encounter. Control transfers that bypass the closing increment can change this behavior.

The original syntax remains supported:

```fortran
===<skip counter:8>===
  call write_output()
===</skip counter>===
```

The current unified parser tracks `skip`, `just_once`, and ordinary block `if` statements together to match closing lines, including nested blocks. The old forms are maintained for existing code.

### Debug printing: `!debugp`

`!debugp` is a convenient way to insert diagnostic output without manually writing a `print` statement. It automatically includes the program/module name and source line number, and labels expressions with their names.

For example:

```fortran
integer :: step = 3
real :: energy = 0.125

!debugp "state", step, energy
step += 1  !debugp step
```

The first `!debugp` generates a `print *` statement reporting `state`, `step = 3`, and `energy = 0.125`, prefixed with the source location (such as `\my_program(5):`). The second appends a debug print to the same line as the assignment and reports the **updated** value of `step`.

You can use `!debugp` with a single variable, a quoted message, or a comma-separated combination of messages and values:

```fortran
!debugp temperature
!debugp "checkpoint reached"
!debugp "iteration", n, "residual", residual
```

The marker resembles a Fortran comment but is converted into executable output by efpp. Remove it or change it to a normal comment when you no longer want the diagnostic print. Argument splitting is lightweight rather than full Fortran parsing, so expressions with embedded commas (for example, array sections or calls with multiple arguments) may need care.

### Predefined source-location macros

| Macro | Replacement |
| --- | --- |
| `__MODULE__` | Outermost recognized program or module name |
| `__FUNC__` | Recognized subprogram name or nested subprogram path |
| `__MODFUNC__` | Program/module name followed by the subprogram path |
| `__LINE__` | Source line number |
| `__MODLINE__` | Program/module name with line number in parentheses |

These macros also expand inside strings, making them useful for diagnostics. Name recognition uses a lightweight parser and does not cover every possible Fortran declaration form.

### User-defined aliases

User-defined aliases are optional. By default, efpp reads `efpp_alias.list` from the current working directory **if the file exists**. If it does not exist, preprocessing continues using built-in substitutions alone. You can also explicitly specify an alias file as the second command-line argument:

```sh
python3 /path/to/efpp/efpp.py demo.ef custom_alias.list > demo.F90
```

An explicitly specified alias file **must exist**; otherwise, efpp reports an error. Likewise, an existing alias file with invalid definitions produces an error.

Alias definitions use the following format:

```text
"do i bulk" => "do i = 1, NXPP"
"__VERSION__" => "2026"
```

Definitions may span multiple lines. Aliases are applied as **ordered text replacements**; a replacement can itself match a later alias. Thus, order can affect the result. Duplicate aliases, unrecognized definitions, and incomplete definitions at end-of-file cause errors. Alias replacement is textual rather than token-aware, so choose distinctive patterns.

### Block comments

Use `!!>` to begin and `!!<` to end a block comment:

```fortran
!!>
call temporarily_disabled()
!!<
```

The preprocessor comments out the enclosed lines without changing the number of lines. Block comments can be nested.

### Other conveniences

**Subsidiary calls:** `-call` lets you append a procedure call to an existing source line:

```text
statement -call update()   ->  statement ;call update()
           -call update()   ->  call update()
```

This is useful for instrumentation; the repository also contains specialized clock annotations.

**`implicit none` check:** efpp performs a simple check near the start of recognized programs or modules. It is **not** a complete syntax check of every Fortran program unit.

## Using efpp with GNU Make

For applications with multiple `.ef` source files, use a pattern rule such as:

```makefile
EFPP = ../efpp.py

%.F90: %.ef
	@rm -f $@.tmp
	@$(EFPP) $< > $@.tmp || { rm -f $@.tmp; exit 1; }
	@mv -f $@.tmp $@
```

Set `EFPP` to the correct script path. An alias file is **not required**: if `efpp_alias.list` exists in the working directory, efpp reads it automatically; otherwise, it runs without user-defined aliases. To require a particular alias file, pass its path as the second argument to efpp in the Makefile rule. Recipe lines must start with a **TAB**. This rule writes the generated Fortran to a temporary file and only replaces the target on successful conversion; on failure, it removes the temporary file and preserves any pre-existing `.F90` file. See [`sample_code/Makefile`](sample_code/Makefile) for a complete example.

## Tests

Run the Python unit tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The tests cover member access, compound assignments, lexical masking, CLI errors (including optional and explicitly specified alias files), and the old and new special-block syntaxes. An additional Fortran program at [`tests/test_blocks.ef`](tests/test_blocks.ef) checks the runtime behavior of `just_once` and `skip` after preprocessing and compilation.

These tests and the sample program are useful regression checks, but they do not establish support for every legal Fortran construct.

## Limitations and compatibility

- efpp is a **lightweight source-to-source preprocessor**, not a complete Fortran lexer or parser. Unusual continuation lines, complex nested syntax, and ambiguous user-defined dot operators may need care.
- The new `if <just_once>` and `if <skip counter:8>` spellings are preferred. The older marker-based spellings remain supported for existing programs.
- The special-block parser tracks a useful subset of Fortran block-`if` syntax. It is not a substitute for compiler syntax checking.
- Most transformations (including `!debugp`) preserve the number and order of source lines. This is useful for diagnostics, but efpp does not produce formal source maps.
- Output is intended for an ordinary Fortran compiler. Any compiler errors in the generated code still need to be resolved in the source or in the corresponding preprocessing rule.

## Editor integration

### Visual Studio Code (recommended starting point)

[Visual Studio Code](https://code.visualstudio.com/) is an optional editor for eFortran; efpp itself does not depend on any editor. Install the [Modern Fortran extension](https://github.com/fortran-lang/vscode-fortran-support) (publisher `fortran-lang`) for Fortran syntax coloring. Associate the eFortran extension `.ef` with free-form Fortran by adding this to your workspace's `.vscode/settings.json`:

```json
{
  "files.associations": {
    "*.ef": "FortranFreeForm"
  }
}
```

The exact example is provided in [`examples/vscode/settings.json`](examples/vscode/settings.json). You may also install `fortls` for ordinary Fortran language-server features, but **eFortran-specific syntax is not understood by standard Fortran language servers**. They may therefore flag valid eFortran extensions before preprocessing; compiler results from generated `.F90` files remain the authoritative check.

Open the repository as a VS Code folder. Use the integrated terminal to build the sample, exactly as you would outside the editor:

```sh
cd sample_code
make
```

#### Jumping from gfortran errors to `.ef` source

The Fortran compiler sees generated `.F90` filenames. VS Code's `problemMatcher` extracts filenames and line numbers from diagnostic text, but **does not itself rename `.F90` paths to `.ef`**. For GNU Fortran, an optional helper is included at [`tools/vscode_make.py`](tools/vscode_make.py), together with a sample [VS Code task](examples/vscode/tasks.json). It relays the original build output, and when gfortran reports an error for `name.F90` and `name.ef` exists alongside it, it emits an additional single-line diagnostic referring to `name.ef`. It also propagates the build's exit code.

For the **included sample**, copy the example settings and task definitions into the repository root's `.vscode/` directory:

```sh
mkdir -p .vscode
cp examples/vscode/settings.json .vscode/settings.json
cp examples/vscode/tasks.json .vscode/tasks.json
```

Then, in VS Code, select **Terminal → Run Build Task** (or the default build-task shortcut). The task runs `make` in `sample_code`; matching gfortran diagnostics can appear in the Problems panel and point to the corresponding `.ef` file. To check the mapping, intentionally introduce a syntax error into a copy of a sample `.ef` file, rebuild, then restore the file.

For your own project, adapt `tasks.json`: set `options.cwd` to the directory used for `make`, point `args[0]` to `vscode_make.py`, and set `problemMatcher.fileLocation` to that same source directory. The helper currently recognizes a common **gfortran multiline diagnostic format**; it is not a general diagnostic parser for all Fortran compilers or all error messages. Line navigation assumes that preprocessing preserves the relevant source line numbers.

### Vim quickfix (optional)

Because efpp preserves line-number correspondence, compiler error locations referring to generated `.F90` files can often be mapped back to the corresponding `.ef` files. For users of Vim's quickfix, this optional `.vimrc` mapping changes `.F90` references in a quickfix list to `.ef`:

```vim
nnoremap <silent> Y :copen<CR>:setlocal modifiable<CR>:%s/\.F90\>/.ef/g<CR>:call histdel('/', -1)<CR>:cbuffer<CR>:cclose<CR>
```

Run `:make` in Vim, use `Y` if needed to rewrite the quickfix filenames, and navigate with `:cnext` or `:cprev`. This assumes matching file base names. It overrides the normal-mode `Y` key and is not a general source-map mechanism.

## Reference

S. Hosoyamada and A. Kageyama, “A Dialect of Modern Fortran for Simulations,” in *Methods and Applications for Modeling and Simulation of Complex Systems*, Communications in Computer and Information Science, vol. 946, pp. 439–448 (2018), Proceedings of AsiaSim 2018.
