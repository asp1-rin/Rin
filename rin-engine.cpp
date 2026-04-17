/*
 * Project: RIN-ENGINE
 * Version: 2.0 (Advanced)
 * Author: asp1-rin
 * * Description: A high-performance memory manipulation engine 
 * designed for process analysis in Android environments.
 */

#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>

using namespace std;

// Display the engine's identity and active modes
void print_header() {
    printf("==================================\n");
    printf("     RIN-ENGINE v2.0 [ADVANCED]   \n");
    printf("  Status: Operational / Mode-Ready \n");
    printf("==================================\n");
}

int main(int argc, char* argv[]) {
    print_header();

    // Validate command-line arguments for proper execution
    if (argc < 4) {
        printf("[Usage Guide]\n");
        printf(" 1. Read    : ./rin-engine r [PID] [Addr]\n");
        printf(" 2. Write   : ./rin-engine w [PID] [Addr] [Value]\n");
        printf(" 3. Monitor : ./rin-engine m [PID] [Addr]\n");
        return 1;
    }

    // Initialize core parameters from input
    char mode = argv[1][0];
    int pid = atoi(argv[2]);
    unsigned long long addr = strtoull(argv[3], NULL, 16);
    
    char path[64];
    sprintf(path, "/proc/%d/mem", pid);

    // Establish link to target process memory with Read/Write access
    int fd = open(path, O_RDWR);
    if (fd == -1) {
        printf("[-] Access Denied: Failed to open memory. Check root privileges.\n");
        return 1;
    }

    // Mode 'r': Precise single-point memory extraction
    if (mode == 'r') {
        int value = 0;
        pread(fd, &value, sizeof(value), addr);
        printf("[+] [DATA] 0x%llX => %d\n", addr, value);
    } 
    // Mode 'w': Real-time memory value injection
    else if (mode == 'w') {
        if (argc < 5) {
            printf("[-] Parameter Error: Missing value for Write mode.\n");
            return 1;
        }
        int newValue = atoi(argv[4]);
        if (pwrite(fd, &newValue, sizeof(newValue), addr) != -1) {
            printf("[+] [SYNC] Success: 0x%llX updated to %d\n", addr, newValue);
        } else {
            printf("[-] [ERR] Write operation failed at targeted address.\n");
        }
    }
    // Mode 'm': Continuous state observation for value shifts
    else if (mode == 'm') {
        int lastValue = -1;
        printf("[*] Monitoring link established at 0x%llX...\n", addr);
        while (true) {
            int currentValue = 0;
            pread(fd, &currentValue, sizeof(currentValue), addr);
            if (currentValue != lastValue) {
                printf("[!] [EVENT] 0x%llX shifted: %d -> %d\n", addr, lastValue, currentValue);
                lastValue = currentValue;
            }
            usleep(100000); // Polling interval: 100ms
        }
    }

    // Clean up resources before termination
    close(fd);
    return 0;
}
