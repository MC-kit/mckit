#ifndef __PY_IMPORT_CALL_EXECUTE_H
#define __PY_IMPORT_CALL_EXECUTE_H

/** Organize debugging of C calls from Python code.
 *
 * Example:
 * https://pythonextensionpatterns.readthedocs.io/en/latest/debugging/debug_in_ide.html
 */

#ifdef __cplusplus
extern "C"
{
#endif

    /** Takes a path and adds it to sys.paths by calling PyRun_SimpleString.
     * This does rather laborious C string concatenation so that it will work in
     * a primitive C environment.
     *
     * return 0 on success, non-zero on failure.
     */
    int add_path_to_sys_module(const char *path);

    /** This imports a Python module and calls a specific function in it.
     *
     * It's arguments are similar to main():
     * argc - Number of strings in argv
     * argv - Expected to be 4 strings:
     *      - Name of the executable.
     *      - Path to the directory that the Python module is in.
     *      - Name of the Python module.
     *      - Name of the function in the module.
     *
     * The Python interpreter will be initialised and the path to the Python module
     * will be added to sys.paths then the module will be imported.
     * The function will be called with no arguments and its return value will be
     * ignored.
     *
     * \return 0 on success, non-zero on failure.
     */
    int import_call_execute(int argc, const char *argv[]);

#ifdef __cplusplus
//    extern "C" {
#endif

#endif // __PY_IMPORT_CALL_EXECUTE_H
