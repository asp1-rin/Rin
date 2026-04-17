/*
 * Project: RIN-ENGINE
 * Version: 3.0 (Full Scanner Integration)
 * Author: asp1-rin
 * Description: Advanced memory engine with automated region scanning,
 * read/write capabilities, and real-time monitoring.
 */

#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

using namespace std;

// Structure to define memory segments from /proc/[PID]/maps
struct MemoryRegion {
    unsigned long long start;
    unsigned long long end;
};

void print_header() {
    printf("==================================\n");
    printf("     RIN-ENGINE v3.0 [SCANNER]    \n");
    printf("  Modes: Scan(s), Read(r), Write(w) \n");
    printf("==================================\n");
}

// Scans the entire memory space of a process for a specific value
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
    
    char line[256];
    while (fgets(line, sizeof(line), maps)) {
        unsigned long long start, end;
        char perms[5];
        // Parse memory region boundaries and permissions
        if (sscanf(line, "%llx-%llx %4s", &start, &end, perms) != 3) continue;

        // Only scan readable regions to avoid segmentation faults or errors
        if (perms[0] != 'r') continue;

        unsigned long long size = end - start;
        int* buffer = (int*)malloc(size);
        if (!buffer) continue;

        if (pread(fd, buffer, size, start) > 0) {
            for (unsigned long long i = 0; i < size / sizeof(int); i++) {
                if (buffer[i] == target_value) {
                    // Output matches for the Python UI to capture
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
        printf("[Usage]\n");
        printf(" Scan  : ./rin-engine s [PID] [Value]\n");
        printf(" Read  : ./rin-engine r [PID] [Addr]\n");
        printf(" Write : ./rin-engine w [PID] [Addr] [Value]\n");
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
        if (fd == -1) return 1;

        if (mode == 'r') {
            int value = 0;
            pread(fd, &value, sizeof(value), addr);
            printf("[+] [DATA] 0x%llX => %d\n", addr, value);
        } 
        else if (mode == 'w') {
            int newValue = atoi(argv[4]);
            pwrite(fd, &newValue, sizeof(newValue), addr);
            printf("[+] [SYNC] Success => %d\n", newValue);
        }
        close(fd);
    }
    return 0;
}
