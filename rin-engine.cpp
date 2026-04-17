/*
 * Project: RIN-ENGINE
 * Version: 3.1 (Cross-Platform Compatibility)
 * Author: asp1-rin
 */

#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

using namespace std;

struct MemoryRegion {
    unsigned long long start;
    unsigned long long end;
};

void print_header() {
    printf("==================================\n");
    printf("     RIN-ENGINE v3.1 [SCANNER]    \n");
    printf("==================================\n");
}

// Portable pread equivalent using lseek and read
ssize_t portable_pread(int fd, void* buf, size_t count, off_t offset) {
    if (lseek(fd, offset, SEEK_SET) == -1) return -1;
    return read(fd, buf, count);
}

// Portable pwrite equivalent using lseek and write
ssize_t portable_pwrite(int fd, const void* buf, size_t count, off_t offset) {
    if (lseek(fd, offset, SEEK_SET) == -1) return -1;
    return write(fd, buf, count);
}

void scan_memory(int pid, int target_value) {
    char map_path[64];
    sprintf(map_path, "/proc/%d/maps", pid);
    FILE* maps = fopen(map_path, "r");
    if (!maps) {
        printf("[-] Error: Unable to open process maps.\n");
        return;
    }

    char mem_path[64];
    sprintf(mem_path, "/proc/%d/mem", pid);
    int fd = open(mem_path, O_RDONLY);
    if (fd == -1) {
        fclose(maps);
        return;
    }
    
    char line[256];
    while (fgets(line, sizeof(line), maps)) {
        unsigned long long start, end;
        char perms[5];
        if (sscanf(line, "%llx-%llx %4s", &start, &end, perms) != 3) continue;
        if (perms[0] != 'r') continue;

        unsigned long long size = end - start;
        int* buffer = (int*)malloc(size);
        if (!buffer) continue;

        if (portable_pread(fd, buffer, size, (off_t)start) > 0) {
            for (unsigned long long i = 0; i < size / sizeof(int); i++) {
                if (buffer[i] == target_value) {
                    printf("[+] MATCH => 0x%llX\n", start + (i * sizeof(int)));
                }
            }
        }
        free(buffer);
    }
    close(fd);
    fclose(maps);
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        print_header();
        return 1;
    }

    char mode = argv[1][0];
    int pid = atoi(argv[2]);
    
    if (mode == 's') {
        int target_val = atoi(argv[3]);
        scan_memory(pid, target_val);
    } 
    else {
        unsigned long long addr = strtoull(argv[3], NULL, 16);
        char path[64];
        sprintf(path, "/proc/%d/mem", pid);
        int fd = open(path, O_RDWR);
        if (fd == -1) {
            // Try Read-Only if RW fails
            fd = open(path, O_RDONLY);
            if (fd == -1) return 1;
        }

        if (mode == 'r') {
            int value = 0;
            portable_pread(fd, &value, sizeof(value), (off_t)addr);
            printf("[+] [DATA] 0x%llX => %d\n", addr, value);
        } 
        else if (mode == 'w') {
            int newValue = atoi(argv[4]);
            portable_pwrite(fd, &newValue, sizeof(newValue), (off_t)addr);
            printf("[+] [SYNC] Success => %d\n", newValue);
        }
        close(fd);
    }
    return 0;
}
