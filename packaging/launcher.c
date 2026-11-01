/* Native app entrypoint. Launch the bundled script without shell interpolation. */
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    uint32_t length = 0;
    (void)_NSGetExecutablePath(NULL, &length);
    char *executable = malloc(length);
    if (executable == NULL || _NSGetExecutablePath(executable, &length) != 0) {
        fputs("Cannot locate Herspers Minecraft launcher.\n", stderr);
        free(executable);
        return 1;
    }
    char *resolved = realpath(executable, NULL);
    free(executable);
    if (resolved == NULL) {
        perror("Cannot resolve Herspers Minecraft launcher");
        return 1;
    }
    char *slash = strrchr(resolved, '/');
    if (slash == NULL) {
        free(resolved);
        return 1;
    }
    *slash = '\0';
    const char suffix[] = "/../Resources/launch.command";
    char *script = malloc(strlen(resolved) + sizeof(suffix));
    char **arguments = calloc((size_t)argc + 2, sizeof(char *));
    if (script == NULL || arguments == NULL) {
        free(resolved);
        free(script);
        free(arguments);
        return 1;
    }
    strcpy(script, resolved);
    strcat(script, suffix);
    free(resolved);
    arguments[0] = "/bin/bash";
    arguments[1] = script;
    for (int index = 1; index < argc; ++index) {
        arguments[index + 1] = argv[index];
    }
    execv("/bin/bash", arguments);
    perror("Cannot start Herspers Minecraft launcher");
    free(script);
    free(arguments);
    return 1;
}
