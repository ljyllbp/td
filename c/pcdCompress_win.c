#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <time.h>
#include <libgen.h>
#include <windows.h>

#define HLOG 16
#define HSIZE (1 << (HLOG))
#define FRST(p) (((p[0]) << 8) | p[1])
#define NEXT(v,p) (((v) << 8) | p[2])

# define ULTRA_FAST 0
# define VERY_FAST 0

# if ULTRA_FAST
#  define IDX(h) ((( h             >> (3*8 - HLOG)) - h  ) & (HSIZE - 1))
# elif VERY_FAST
#  define IDX(h) ((( h             >> (3*8 - HLOG)) - h*5) & (HSIZE - 1))
# else
#  define IDX(h) ((((h ^ (h << 5)) >> (3*8 - HLOG)) - h*5) & (HSIZE - 1))
# endif

# define expect(expr,value)         __builtin_expect ((expr),(value))
#define expect_false(expr) expect ((expr) != 0, 0)
#define expect_true(expr)  expect ((expr) != 0, 1)

# define SET_ERRNO(n) *err = (n)

typedef unsigned int LZF_HSLOT;
typedef LZF_HSLOT LZF_STATE[1 << (HLOG)];

typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long uint64;

typedef signed char int8;
typedef short int int16;
typedef int int32;
typedef long long int64;

typedef float float32;
typedef double float64;

typedef int bool;
#define true 1
#define false 0
#define PCD_S_ROOT "/.TD_PCD_FILES/"

#define ascii 0
#define binary 1
#define binary_compressed 2
#define BLOCKPOINTCOUNT 1000000
#define BLOCKCHARCOUNT 1048576

struct  Data{
    char *buf;
    char *resbuf;
    uint32 resbuflen;
    uint32 len;
    struct Data *nextData;
};

struct Field{
    bool exist;
    char name[20];
    char type[2];
    int32 count;
    int32 size;
    int32 index;
    int32 offset;
    struct Data data;
};

struct PcdInfo{
    uint32 pointCount;
    uint8 offset;
    uint64 bufLen;
    uint8 type;
    uint8 fieldCount;
    uint8 aPointSize;
    bool isCompressed;
    bool isChange;

    uint8 float32Count;
    uint8 uint32Count;
    uint8 uint8Count;
    

    struct Data data;

    struct Field ** fields;
    
    // struct Field r;  // U 1
    // struct Field g;  // U 1
    // struct Field b;  // U 1

    struct Field rgb; // F 4 or U 4

    struct Field intensity; // F 4 or U 1

    struct Field x;  // F 4
    struct Field y;  // F 4
    struct Field z;  // F 4

    // struct Field normal_x;  // F 4
    // struct Field normal_y;  // F 4
    // struct Field normal_z;  // F 4
};

unsigned int lzf_compress(const void *const in_data, unsigned int in_len, void *out_data, unsigned int out_len){
    
    unsigned int htab[65536];

    const uint8 *ip = (const uint8 *)in_data;
    uint8 *op = (uint8 *)out_data;
    const uint8 *in_end  = ip + in_len;
    uint8 *out_end = op + out_len;
    const uint8 *ref;

    unsigned long off;
    unsigned int hval;
    int lit;

    

    if (!in_len || !out_len){
        return 0;
    }
    
    lit = 0; 
    op++;
    hval = FRST (ip);

     

    while (ip < in_end - 2){
        unsigned int *hslot;
        hval = NEXT (hval, ip);
        hslot = htab + IDX (hval);
        ref = *hslot + ((const uint8 *)in_data); 
        *hslot = ip - ((const uint8 *)in_data);

        if (
            1
            && (off = ip - ref - 1) < 8192
            && ref > (uint8 *)in_data
            && ref[2] == ip[2]
            && ((ref[1] << 8) | ref[0]) == ((ip[1] << 8) | ip[0])
        ){
            unsigned int len = 2;
            unsigned int maxlen = in_end - ip - len;
            maxlen = maxlen > 264 ? 264 : maxlen;

            if (expect_false (op + 3 + 1 >= out_end)){
                if (op - !lit + 3 + 1 >= out_end){
                    return 0;
                }
            }

            op [- lit - 1] = lit - 1;
            op -= !lit;

            for (;;){
                if (expect_true (maxlen > 16)){
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;

                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;

                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;

                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                    len++; if (ref [len] != ip [len]) break;
                }

                do{
                    len++;
                }while (len < maxlen && ref[len] == ip[len]);

                break;
            }
            
            len -= 2;
            ip++;

            if (len < 7){
                *op++ = (off >> 8) + (len << 5);
            }else{
                *op++ = (off >> 8) + (  7 << 5);
                *op++ = len - 7;
            }

            *op++ = off;

            lit = 0; 
            op++;

            ip += len + 1;

            if (expect_false (ip >= in_end - 2)){
                break;
            }
            
            if (ULTRA_FAST || VERY_FAST){
                --ip;
            
                if (VERY_FAST && !ULTRA_FAST){
                    --ip;
                }

                hval = FRST (ip);

                hval = NEXT (hval, ip);
                htab[IDX (hval)] = ip - ((const uint8 *)in_data);
                ip++;

                if (VERY_FAST && !ULTRA_FAST){
                    hval = NEXT (hval, ip);
                    htab[IDX (hval)] = ip - ((const uint8 *)in_data);
                    ip++;
                }
            }else{

                ip -= len + 1;
                do
                    {
                    hval = NEXT (hval, ip);
                    htab[IDX (hval)] = ip - ((const uint8 *)in_data);
                    ip++;
                    }
                while (len--);
            }
        }else{
            if (expect_false (op >= out_end)){
                return 0;
            }
            
            lit++; 
            *op++ = *ip++;

            if (expect_false (lit == 32)){
                op [- lit - 1] = lit - 1; 
                lit = 0; 
                op++; 
            }
        }
    }

    if (op + 3 > out_end){
        return 0;
    }

    while (ip < in_end)
    {
        lit++; *op++ = *ip++;

        if (expect_false (lit == 32)){
            op [- lit - 1] = lit - 1;
            lit = 0; 
            op++;
        }
    }

    op [- lit - 1] = lit - 1;
    op -= !lit;

    return op - (uint8 *)out_data;
}

unsigned int lzf_decompress(const void *const in_data, unsigned int in_len, void *out_data, unsigned int out_len, int *err){
    uint8 const *ip = (const uint8 *)in_data;
    uint8 *op = (uint8 *)out_data;
    uint8 const *const in_end  = ip + in_len;
    uint8 *const out_end = op + out_len;
    do{
        unsigned int ctrl = *ip++;
        if (ctrl < (1 << 5)){
            ctrl++;
            if (op + ctrl > out_end){
                SET_ERRNO (E2BIG);
                return 0;
            }

            if (ip + ctrl > in_end){
              SET_ERRNO (EINVAL);
              return 0;
            }

            switch (ctrl){
              case 32: *op++ = *ip++; case 31: *op++ = *ip++; case 30: *op++ = *ip++; case 29: *op++ = *ip++;
              case 28: *op++ = *ip++; case 27: *op++ = *ip++; case 26: *op++ = *ip++; case 25: *op++ = *ip++;
              case 24: *op++ = *ip++; case 23: *op++ = *ip++; case 22: *op++ = *ip++; case 21: *op++ = *ip++;
              case 20: *op++ = *ip++; case 19: *op++ = *ip++; case 18: *op++ = *ip++; case 17: *op++ = *ip++;
              case 16: *op++ = *ip++; case 15: *op++ = *ip++; case 14: *op++ = *ip++; case 13: *op++ = *ip++;
              case 12: *op++ = *ip++; case 11: *op++ = *ip++; case 10: *op++ = *ip++; case  9: *op++ = *ip++;
              case  8: *op++ = *ip++; case  7: *op++ = *ip++; case  6: *op++ = *ip++; case  5: *op++ = *ip++;
              case  4: *op++ = *ip++; case  3: *op++ = *ip++; case  2: *op++ = *ip++; case  1: *op++ = *ip++;
            }
        }else{
            unsigned int len = ctrl >> 5;
            uint8 *ref = op - ((ctrl & 0x1f) << 8) - 1;
            if (ip >= in_end){
              SET_ERRNO (EINVAL);
              return 0;
            }
            if (len == 7){
                len += *ip++;
                if (ip >= in_end){
                  SET_ERRNO (EINVAL);
                  return 0;
                }
            }
            ref -= *ip++;
            if (op + len + 2 > out_end){
              SET_ERRNO (E2BIG);
              return 0;
            }
            if (ref < (uint8 *)out_data){
              SET_ERRNO (EINVAL);
              return 0;
            }
            switch (len){
                default:
                    len += 2;

                    if (op >= ref + len){
                        memcpy (op, ref, len);
                        op += len;
                    }else{
                        do{
                            *op++ = *ref++;
                        }while (--len);
                    }
                    break;
                case 9: *op++ = *ref++;
                case 8: *op++ = *ref++;
                case 7: *op++ = *ref++;
                case 6: *op++ = *ref++;
                case 5: *op++ = *ref++;
                case 4: *op++ = *ref++;
                case 3: *op++ = *ref++;
                case 2: *op++ = *ref++;
                case 1: *op++ = *ref++;
                case 0: *op++ = *ref++;
                        *op++ = *ref++;
            }
        }
    }while(ip < in_end);
    return op - (uint8 *)out_data;
}

void initField(struct Field *field){
    field->exist = false;
    field->data.buf = NULL;
    field->data.resbuf = NULL;
    field->data.nextData = NULL;
}

void initPcdInfo(struct PcdInfo *pcdInfo){
    // initField(&(pcdInfo->r));
    // initField(&(pcdInfo->g));
    // initField(&(pcdInfo->b));
    initField(&(pcdInfo->rgb));
    initField(&(pcdInfo->intensity));
    initField(&(pcdInfo->x));
    initField(&(pcdInfo->y));
    initField(&(pcdInfo->z));
    // initField(&(pcdInfo->normal_x));
    // initField(&(pcdInfo->normal_y));
    // initField(&(pcdInfo->normal_z));

    pcdInfo->fields = NULL;
    pcdInfo->data.nextData = NULL;
    pcdInfo->data.buf = NULL;
    pcdInfo->data.resbuf = NULL;

}

struct StrSplitRes{
    int total;
    char **res;
};

void strSplitResFree(struct StrSplitRes * strSplitRes){
    for (int i = 0; i < strSplitRes->total;i++){
        free(strSplitRes->res[i]);
        strSplitRes->res[i] = NULL;
    }

    free(strSplitRes->res);
    strSplitRes->res = NULL;

    strSplitRes->total = 0;
    
}

void cp(char * src, char **dist, int ip, int step){
    *dist = NULL;
    *dist = (char *) malloc((step + 1) * sizeof(char));
    if (*dist == NULL){
        printf("memeroy error\n");
        exit(1);
    }
    for (int i = 0; i < step; i++){
        (*dist)[i] = src[ip+i];
    }
    (*dist)[step] = '\0';
}

void split(struct StrSplitRes *strSplitRes,char *str, char *delimiter){

    int strLen;
    int delimiterLen = strlen(delimiter);
    strLen = strlen(str);
    

    strSplitRes->total = 0;
    strSplitRes->res = NULL;
    strSplitRes->res = (char **)malloc(100 * sizeof(char *));
    if (strSplitRes->res == NULL){
        printf("memory error\n");
        exit(1);
    }

    if (expect_false(delimiterLen == 0)){
        printf("The delimiter length should be greater than one\n");
        exit(1);
    }else if (expect_false(strLen <= delimiterLen)){
        if (expect_false(strcmp(str , delimiter) == 0)){
            strSplitRes->total = 2;

            strSplitRes->res[0] = NULL;
            strSplitRes->res[0] = (char *)malloc(sizeof(char));
            if (strSplitRes->res[0] == NULL){
                printf("memory error\n");
                exit(1);
            }
            strSplitRes->res[0][0] = '\0';

            strSplitRes->res[1] = NULL;
            strSplitRes->res[1] = (char *)malloc(sizeof(char));
            if (strSplitRes->res[1] == NULL){
                printf("memory error\n");
                exit(1);
            }
            strSplitRes->res[1][0] = '\0';
            
        }else{
            strSplitRes->total = 1;

            strSplitRes->res[0] = NULL;
            strSplitRes->res[0] = (char *)malloc((strLen+1) * sizeof(char));
            if (strSplitRes->res[0] == NULL){
                printf("memory error\n");
                exit(1);
            }
            memset(strSplitRes->res[0],0,strLen+1);
            strcpy(strSplitRes->res[0],str);
        }
    }else{
        int ip = 0;
        bool same = false;
        for (int i=0; i<strLen-delimiterLen+1; i++){
            same = true;
            for (int j=0; j<delimiterLen; j++){
                if (expect_false(str[i+j] == delimiter[j])){
                    continue;
                }else{
                    same = false;
                    break;
                }
            }
            if (expect_false(same)){
                
                if (expect_false(ip == i)){
                    strSplitRes->res[strSplitRes->total] = NULL;
                    strSplitRes->res[strSplitRes->total] = (char *)malloc(sizeof(char));
                    if (strSplitRes->res[strSplitRes->total] == NULL){
                        printf("memory error\n");
                        exit(1);
                    }
                    strSplitRes->res[strSplitRes->total][0] = '\0' ;

                }else{
                    cp(str, &(strSplitRes->res[strSplitRes->total]), ip, i - ip) ;
                }
                ip = i + delimiterLen;
                i = i + delimiterLen -1;
                strSplitRes->total += 1;
            }
        }
        if (ip != strLen){
            cp(str, &(strSplitRes->res[strSplitRes->total]), ip, strLen - ip);
        }else{
            strSplitRes->res[strSplitRes->total] = NULL;
            strSplitRes->res[strSplitRes->total] = (char *)malloc(sizeof(char));
            if (strSplitRes->res[strSplitRes->total] == NULL){
                printf("memory error\n");
                exit(1);
            }
            strSplitRes->res[strSplitRes->total][0] = '\0' ;
        }
        strSplitRes->total += 1;
    }
}

void strip(char *line){
    int lineLen = strlen(line);
    int noUseStrLen = 0;
    for (int i=lineLen-1; i>=0; i--){
        if (line[i] == '\r' || line[i] == '\n'){
            noUseStrLen++;
        }else{
            break;
        }
    }
    line[lineLen - noUseStrLen] = '\0';
}

bool endwith(char *str, char *end){
    int strLen, endLen, offset;
    strLen = strlen(str);
    endLen = strlen(end);
    
    if (endLen > strLen){
        return false;
    }
    if (endLen == 0){
        return false;
    }
    offset = strLen - endLen;

    for (int i=0; i < endLen; i++){
        if (str[i+offset] != end[i]){
            return false;
        }
    }
    return true;
}

bool startwith(char *str, char *start){
    int strLen, startLen;
    strLen = strlen(str);
    startLen = strlen(start);
    
    if (startLen > strLen){
        return false;
    }
    if (startLen == 0){
        return false;
    }

    for (int i=0; i < startLen; i++){
        if (str[i] != start[i]){
            return false;
        }
    }
    return true;
}

void checkField(struct Field *field, char *name,char type, int32 size){
    
    if (field->exist){
        if (field->count != 1){
            printf("%s count != 1\n", name);
            exit(1);
        }
        
        if (field->size != size){
            printf("%s size != %d\n", name, size);
            exit(1);
        }

        if (field->type[0] != type){
            printf("%s type != %c\n", name, type);
            exit(1);
        }

    }else{
        if (!(strcmp("x",name)) || !(strcmp("y",name)) || !(strcmp("z",name))){
            printf("%s not exsit\n", name);
            exit(1);
        }
    }

}

void checkPcdInfo(struct PcdInfo *pcdinfo){
    checkField(&(pcdinfo->x), "x", 'F', 4);
    checkField(&(pcdinfo->y), "y", 'F', 4);
    checkField(&(pcdinfo->z), "z", 'F', 4);
    // checkField(&(pcdinfo->r), "r", 'U', 1);
    // checkField(&(pcdinfo->g), "g", 'U', 1);
    // checkField(&(pcdinfo->b), "b", 'U', 1);

    if (pcdinfo->rgb.exist){
        if (pcdinfo->rgb.type[0] == 'F'){
            checkField(&(pcdinfo->rgb), "rgb", 'F', 4);
        }else if(pcdinfo->rgb.type[0] == 'U'){
            checkField(&(pcdinfo->rgb), "rgb", 'U', 4);
        }else{
            printf("rgb type != F or U\n");
            exit(1);
        }
    }

    if (pcdinfo->intensity.exist){
        if (pcdinfo->intensity.type[0] == 'F'){
            checkField(&(pcdinfo->intensity), "intensity", 'F', 4);
        }else if(pcdinfo->intensity.type[0] == 'U'){
            checkField(&(pcdinfo->intensity), "intensity", 'U', 1);
        }else{
            printf("intensity type != F or U\n");
            exit(1);
        }
        
    }
    
    // checkField(&(pcdinfo->normal_x), "normal_x", 'F', 4);
    // checkField(&(pcdinfo->normal_y), "normal_y", 'F', 4);
    // checkField(&(pcdinfo->normal_z), "normal_z", 'F', 4);

    // if (pcdinfo->r.exist != pcdinfo->g.exist || pcdinfo->r.exist != pcdinfo->b.exist){
    //     printf("r g b should exist simultaneously\n");
    //     exit(1);
    // }

    // if (pcdinfo->normal_x.exist != pcdinfo->normal_y.exist || pcdinfo->normal_x.exist != pcdinfo->normal_z.exist){
    //     printf("normal_x normal_y normal_z should exist simultaneously\n");
    //     exit(1);
    // }

    if (pcdinfo->pointCount > 20000000){
        printf("PCD files with points exceeding 20000000 are not supported\n");
        exit(1);
    }
    if (pcdinfo->pointCount <= 0){
        printf("PCD files with points below 0 are not supported\n");
        exit(1);
    }
}

void fillField(struct Field *field, int32 size, char type, int32 count, int32 index, int32 offset, char *name){
    field->exist = true;
    field->size = size;
    field->type[0] = type;
    field->type[1] = '\0';
    field->count = count;
    field->index = index;
    field->offset = offset;
    strcpy(field->name,name);

}

void readPcdHead(struct PcdInfo *pcdinfo, FILE *fp, bool forceCompressed){
    initPcdInfo(pcdinfo);

    char line[1000];
    uint8 lineCount = 15;
    struct StrSplitRes strSplitRes;
    char files[4][20][20];
    int filesCount = 0;

    while (fgets(line, 1000, fp) != NULL){
        strip(line);
        split(&strSplitRes, line, " ");

        if (strcmp(strSplitRes.res[0],"DATA")==0){
            if (strcmp(strSplitRes.res[1], "ascii")==0){
                pcdinfo->type = ascii;
            }else if (strcmp(strSplitRes.res[1], "binary")==0){
                pcdinfo->type = binary;
            }else if (strcmp(strSplitRes.res[1], "binary_compressed")==0){
                pcdinfo->type = binary_compressed;
            }else{
                printf("pcd type error\n");
                exit(1);
            }
            strSplitResFree(&strSplitRes);
            break;
        }else if(strcmp(strSplitRes.res[0],"FIELDS")==0){
            for (int i=1; i<strSplitRes.total;i++){
                strcpy(files[0][i-1] , strSplitRes.res[i]);
                filesCount++;
            }
        }else if(strcmp(strSplitRes.res[0],"SIZE")==0){
            for (int i=1; i<strSplitRes.total;i++){
                strcpy(files[1][i-1] , strSplitRes.res[i]);
            }
        }
        else if(strcmp(strSplitRes.res[0],"TYPE")==0){
            for (int i=1; i<strSplitRes.total;i++){
                strcpy(files[2][i-1] , strSplitRes.res[i]);
            }
        }
        else if(strcmp(strSplitRes.res[0],"COUNT")==0){
            for (int i=1; i<strSplitRes.total;i++){
                strcpy(files[3][i-1] , strSplitRes.res[i]);
            }
        }
        else if(strcmp(strSplitRes.res[0],"POINTS")==0){
            pcdinfo->pointCount = (uint32)atoi(strSplitRes.res[1]);
        }
        strSplitResFree(&strSplitRes);
        lineCount--;
        if (lineCount <=0){
            break;
        }
    }
    
    int32 index = 0;
    int32 count = 0;
    int32 offset = 0;
    int32 size = 0;
    pcdinfo->fieldCount = 0;
    pcdinfo->isChange = false;

    for (int i=0; i<filesCount; i++){
        count = (int32)atoi(files[3][i]);
        size = (int32)atoi(files[1][i]);
        // if (!strcmp(files[0][i], "r")){
        //     fillField(&(pcdinfo->r), size, files[2][i][0], count, index, offset, "r");
        //     pcdinfo->fieldCount++;
        // }else if (!strcmp(files[0][i], "g")){
        //     fillField(&(pcdinfo->g), size, files[2][i][0], count, index, offset, "g");
        //     pcdinfo->fieldCount++;
        // }else if (!strcmp(files[0][i], "b")){
        //     fillField(&(pcdinfo->b), size, files[2][i][0], count, index, offset, "b");
        //     pcdinfo->fieldCount++;
        // }else 
        if (!strcmp(files[0][i], "rgb")){
            fillField(&(pcdinfo->rgb), size, files[2][i][0], count, index, offset, "rgb");
            pcdinfo->fieldCount++;
        }else if (!strcmp(files[0][i], "intensity")){
            fillField(&(pcdinfo->intensity), size, files[2][i][0], count, index, offset, "intensity");
            pcdinfo->fieldCount++;
        }else if (!strcmp(files[0][i], "x")){
            fillField(&(pcdinfo->x), size, files[2][i][0], count, index, offset, "x");
            pcdinfo->fieldCount++;
        }else if (!strcmp(files[0][i], "y")){
            fillField(&(pcdinfo->y), size, files[2][i][0], count, index, offset, "y");
            pcdinfo->fieldCount++;
        }else if (!strcmp(files[0][i], "z")){
            fillField(&(pcdinfo->z), size, files[2][i][0], count, index, offset, "z");
            pcdinfo->fieldCount++;
        // }else if (!strcmp(files[0][i], "normal_x")){
        //     fillField(&(pcdinfo->normal_x), size, files[2][i][0], count, index, offset, "normal_x");
        //     pcdinfo->fieldCount++;
        // }else if (!strcmp(files[0][i], "normal_y")){
        //     fillField(&(pcdinfo->normal_y), size, files[2][i][0], count, index, offset, "nromal_y");
        //     pcdinfo->fieldCount++;
        // }else if (!strcmp(files[0][i], "normal_z")){
        //     fillField(&(pcdinfo->normal_z), size, files[2][i][0], count, index, offset, "normal_z");
        //     pcdinfo->fieldCount++;
        }else{
            pcdinfo->isChange = true;
        }
        index += count;
        offset = offset + size * count;
    }

    pcdinfo->offset = (uint8)offset;
    pcdinfo->bufLen = (uint64)offset * (uint64)pcdinfo->pointCount;
    pcdinfo->aPointSize = 0;
    pcdinfo->isCompressed = false;

    pcdinfo->fields = NULL;
    pcdinfo->fields = (struct Field **)malloc(pcdinfo->fieldCount * sizeof(struct Field *));
    if (pcdinfo->fields == NULL){
        printf("memory error\n");
    }
    // F4 U4 i1 

    pcdinfo->float32Count = 0;
    pcdinfo->uint32Count = 0;
    pcdinfo->uint8Count = 0;

    int fieldsip = 0;
    pcdinfo->fields[0] = &(pcdinfo->x);
    pcdinfo->fields[1] = &(pcdinfo->y);
    pcdinfo->fields[2] = &(pcdinfo->z);

    pcdinfo->aPointSize += pcdinfo->x.size;
    pcdinfo->aPointSize += pcdinfo->y.size;
    pcdinfo->aPointSize += pcdinfo->z.size;

    pcdinfo->float32Count += 3;
    fieldsip += 3;

    // if (pcdinfo->normal_x.exist){
    //     pcdinfo->aPointSize += pcdinfo->normal_x.size;
    //     pcdinfo->aPointSize += pcdinfo->normal_y.size;
    //     pcdinfo->aPointSize += pcdinfo->normal_z.size;
    //     pcdinfo->fields[fieldsip] = &(pcdinfo->normal_x);
    //     pcdinfo->fields[fieldsip+1] = &(pcdinfo->normal_y);
    //     pcdinfo->fields[fieldsip+2] = &(pcdinfo->normal_z);
    //     pcdinfo->float32Count += 3;
    //     fieldsip += 3;
    // }

    if (pcdinfo->intensity.exist && pcdinfo->intensity.type[0] == 'F'){
        pcdinfo->isCompressed = true;
        pcdinfo->aPointSize += pcdinfo->intensity.size;
        pcdinfo->fields[fieldsip] = &(pcdinfo->intensity);
        fieldsip += 1;
        pcdinfo->float32Count += 1;
    }

    if (pcdinfo->rgb.exist && pcdinfo->rgb.type[0] == 'F'){
        pcdinfo->aPointSize += pcdinfo->rgb.size;
        pcdinfo->fields[fieldsip] = &(pcdinfo->rgb);
        fieldsip += 1;
        pcdinfo->float32Count += 1;
    }

    if (pcdinfo->rgb.exist && pcdinfo->rgb.type[0] == 'U'){
        pcdinfo->aPointSize += pcdinfo->rgb.size;
        pcdinfo->fields[fieldsip] = &(pcdinfo->rgb);
        fieldsip += 1;
        pcdinfo->uint32Count += 1;
    }

    if (pcdinfo->intensity.exist && pcdinfo->intensity.type[0] == 'U'){
        pcdinfo->aPointSize += pcdinfo->intensity.size;
        pcdinfo->fields[fieldsip] = &(pcdinfo->intensity);
        fieldsip += 1;
        pcdinfo->uint8Count += 1;
    }

    // if (pcdinfo->r.exist){
    //     pcdinfo->aPointSize += pcdinfo->r.size;
    //     pcdinfo->aPointSize += pcdinfo->g.size;
    //     pcdinfo->aPointSize += pcdinfo->b.size;
    //     pcdinfo->fields[fieldsip] = &(pcdinfo->r);
    //     pcdinfo->fields[fieldsip+1] = &(pcdinfo->g);
    //     pcdinfo->fields[fieldsip+2] = &(pcdinfo->b);
    //     pcdinfo->uint8Count += 1;
    // }

    if (forceCompressed == true){
        pcdinfo->isCompressed = true;
    }

    if (pcdinfo->pointCount > 20000000 ){
        pcdinfo->isCompressed = false;
    }

}

void allocateMemoryByField(struct Field *field, uint32 pointCount){
    if (!(field->exist)){
        return;
    }
    
    if (pointCount <= BLOCKPOINTCOUNT){
        field->data.len = pointCount;
        field->data.nextData = NULL;
        field->data.buf = NULL;
        field->data.buf = (char *) malloc(pointCount * field->size);
        field->data.resbuf = NULL;
        if (field->data.buf == NULL){
            printf("memory error\n");
            exit(1);
        }
        return;
    }

    field->data.len = BLOCKPOINTCOUNT;
    field->data.nextData = NULL;
    field->data.resbuf = NULL;
    field->data.buf = NULL;
    field->data.buf = (char *) malloc(BLOCKPOINTCOUNT * field->size);
    if (field->data.buf == NULL){
        printf("memory error\n");
        exit(1);
    }
    pointCount -= BLOCKPOINTCOUNT;

    int32 blockPointCount;
    struct Data *nowData = &(field->data);;
    struct Data *nextData = NULL;

    
    while (pointCount >0){
        if (pointCount > BLOCKPOINTCOUNT){
            blockPointCount = BLOCKPOINTCOUNT;
            pointCount -= BLOCKPOINTCOUNT;
        }else{
            blockPointCount = pointCount;
            pointCount = 0;
        }

        nextData = NULL;
        nextData = (struct Data *)malloc(sizeof(struct Data));
        if (nextData == NULL){
            printf("memory error\n");
            exit(1);
        }
        nextData->len = blockPointCount;
        nextData->nextData = NULL;
        nextData->resbuf = NULL;
        nextData->buf = NULL;
        nextData->buf = (char *) malloc(blockPointCount * field->size);
        if (nextData->buf==NULL){
            printf("memory error\n");
            exit(1);
        }
        nowData->nextData = nextData;
        nowData = nextData;
        
    }

}

void allocateMemoryPcdInfo(struct PcdInfo *pcdinfo){
    if (pcdinfo->isCompressed){
        // allocateMemoryByField(&(pcdinfo->r), pcdinfo->pointCount);
        // allocateMemoryByField(&(pcdinfo->g), pcdinfo->pointCount);
        // allocateMemoryByField(&(pcdinfo->b), pcdinfo->pointCount);
        allocateMemoryByField(&(pcdinfo->rgb), pcdinfo->pointCount);
        allocateMemoryByField(&(pcdinfo->intensity), pcdinfo->pointCount);
        allocateMemoryByField(&(pcdinfo->x), pcdinfo->pointCount);
        allocateMemoryByField(&(pcdinfo->y), pcdinfo->pointCount);
        allocateMemoryByField(&(pcdinfo->z), pcdinfo->pointCount);
        // allocateMemoryByField(&(pcdinfo->normal_x), pcdinfo->pointCount);
        // allocateMemoryByField(&(pcdinfo->normal_y), pcdinfo->pointCount);
        // allocateMemoryByField(&(pcdinfo->normal_z), pcdinfo->pointCount);
    }else{
        uint32 pointCount = pcdinfo->pointCount;
        if (pointCount <= BLOCKPOINTCOUNT){
            pcdinfo->data.resbuflen = pointCount * pcdinfo->aPointSize;
            pcdinfo->data.len = pointCount;
            pcdinfo->data.buf = NULL;
            pcdinfo->data.nextData = NULL;
            pcdinfo->data.resbuf = NULL;
            pcdinfo->data.resbuf = (char *) malloc(pcdinfo->data.resbuflen);
            if (pcdinfo->data.resbuf == NULL){
                printf("memory error\n");
                exit(1);
            }
            return;
        }

        pcdinfo->data.len = BLOCKPOINTCOUNT;
        pcdinfo->data.resbuflen = BLOCKPOINTCOUNT * pcdinfo->aPointSize;
        pcdinfo->data.buf = NULL;
        pcdinfo->data.nextData = NULL;
        pcdinfo->data.resbuf = NULL;
        pcdinfo->data.resbuf = (char *) malloc(pcdinfo->data.resbuflen);
        if (pcdinfo->data.resbuf == NULL){
            printf("memory error\n");
            exit(1);
        }
        pointCount -= BLOCKPOINTCOUNT;

        int32 blockPointCount;
        struct Data *nowData;
        struct Data *nextData = NULL;
        nowData = &(pcdinfo->data);

        while (pointCount >0){
            if (pointCount > BLOCKPOINTCOUNT){
                blockPointCount = BLOCKPOINTCOUNT;
                pointCount -= BLOCKPOINTCOUNT;
            }else{
                blockPointCount = pointCount;
                pointCount = 0;
            }

            nextData = NULL;
            nextData = (struct Data *)malloc(sizeof(struct Data));
            if (nextData == NULL){
                printf("memory error\n");
                exit(1);
            }

            nextData->resbuflen = blockPointCount * pcdinfo->aPointSize;
            nextData->len = blockPointCount;
            nextData->nextData = NULL;
            nextData->buf = NULL;
            nextData->resbuf = NULL;
            nextData->resbuf = (char *) malloc(nextData->resbuflen);
            if (nextData->resbuf == NULL){
                printf("memory error\n");
                exit(1);
            }
            nowData->nextData = nextData;
            nowData = nextData;
            
        }
    }
    
}

void destroyMemoryByField(struct Field *field){
    // size_t size;
    if (!(field->exist)){
        return;
    }
    struct Data *nowData = &(field->data);
    struct Data *nextData = NULL;

    
    free(nowData->buf);
    nowData->buf = NULL;
    

    free(nowData->resbuf);
    nowData->resbuf = NULL;
    

    nextData = nowData->nextData;
    nowData = nextData;

    while (nowData != NULL){
        nextData = nowData->nextData;

        free(nowData->buf);
        nowData->buf = NULL;
        
        free(nowData->resbuf);
        nowData->resbuf = NULL;
        
        free(nowData);
        nowData = NULL;
        nowData = nextData;
    }
}

void destroyMemoryPcdInfo(struct PcdInfo *pcdinfo){
    if (pcdinfo->isCompressed){
        // destroyMemoryByField(&(pcdinfo->r));
        // destroyMemoryByField(&(pcdinfo->g));
        // destroyMemoryByField(&(pcdinfo->b));
        destroyMemoryByField(&(pcdinfo->rgb));
        destroyMemoryByField(&(pcdinfo->intensity));
        destroyMemoryByField(&(pcdinfo->x));
        destroyMemoryByField(&(pcdinfo->y));
        destroyMemoryByField(&(pcdinfo->z));
        // destroyMemoryByField(&(pcdinfo->normal_x));
        // destroyMemoryByField(&(pcdinfo->normal_y));
        // destroyMemoryByField(&(pcdinfo->normal_z));
    } else{
        struct Data *nowData = &(pcdinfo->data);
        struct Data *nextData = NULL;

        free(nowData->buf);
        nowData->buf = NULL;
        
        free(nowData->resbuf);
        nowData->resbuf = NULL;
        
        nextData = nowData->nextData;
        nowData = nextData;

        while (nowData != NULL){
            nextData = nowData->nextData;
            
            free(nowData->buf);
            nowData->buf = NULL;
            
            free(nowData->resbuf);
            nowData->resbuf = NULL;
            
            free(nowData);
            nowData = NULL;
            nowData = nextData;
        }
    }
}

void readPcdDataAscii(struct PcdInfo *pcdinfo, FILE *fp){
    int pcdHeadLength,pcdFileLength,dataLength,bufLength;
    char c;
    char *buf = NULL;
    char line[200];
    int lineip = 0;
    struct StrSplitRes strSplitRes;

    pcdHeadLength = ftell(fp);

    fseek(fp, 0, SEEK_END);
    pcdFileLength = ftell(fp);
    
    
    fseek(fp, pcdHeadLength, SEEK_SET);
    
    dataLength = pcdFileLength-pcdHeadLength;

    struct Data **datas = NULL;
    datas = (struct Data **) malloc (pcdinfo->fieldCount * sizeof(struct Data *));
    if (datas == NULL){
        printf("memory error\n");
        exit(1);
    }
    int32 *index = NULL;
    index = (int32 *) malloc (pcdinfo->fieldCount * sizeof(int32));
    if (index == NULL){
        printf("memory error\n");
        exit(1);
    }

    for (int i = 0; i < pcdinfo->fieldCount; i++){
        datas[i] = &(pcdinfo->fields[i]->data);
        index[i] = pcdinfo->fields[i]->index;
    }

    // 所有可能读取字段 x y z intensity normal_x normal_y normal_z r g b
    // 读取字段 x y z intensity r g b
    // 读取顺序 F4 U4 I1

    uint32 len = pcdinfo->x.data.len;
    uint32 bufsIp = 0;
    float32 float32Num;
    uint32 uint32Num;
    uint8 uint8Num;
    int32 indexNum;
    int32 bufIp;
    int32 binaryBufIp = 0;
    uint32 lineCount = 0;

    struct Data *nowData = &(pcdinfo->data);

    char *float32NumIp = (char *)(&float32Num);
    char *float32Numbuf0 = float32NumIp++;
    char *float32Numbuf1 = float32NumIp++;
    char *float32Numbuf2 = float32NumIp++;
    char *float32Numbuf3 = float32NumIp;

    char *uint8Numbuf = (char *)(&uint8Num);

    char *uint32NumIp = (char *)(&uint32Num);
    char *uint32Numbuf0 = uint32NumIp++;
    char *uint32Numbuf1 = uint32NumIp++;
    char *uint32Numbuf2 = uint32NumIp++;
    char *uint32Numbuf3 = uint32NumIp;

    
    uint8 float32Count = pcdinfo->float32Count;
    uint8 uint32Count = pcdinfo->uint32Count;
    uint8 uint8Count = pcdinfo->uint8Count;
    
    uint8 float32Start = 0;
    uint8 float32End = float32Count;
    uint8 uint32Start = float32End;
    uint8 uint32End = uint32Start + uint32Count;
    uint8 uint8Start = uint32End;
    uint8 uint8End = uint8Start + uint8Count;
    
    while (dataLength > 0){
        if (dataLength <= BLOCKCHARCOUNT){
            bufLength = dataLength;
            dataLength = 0;
        }else{
            bufLength = BLOCKCHARCOUNT;
            dataLength -= BLOCKCHARCOUNT;
        }

        buf = NULL;
        buf = (char *)malloc((bufLength + 1) * sizeof(char));
        if (buf == NULL){
            printf("memory error\n");
            exit(1);
        }
        fread(buf, 1, bufLength, fp);
        if (dataLength == 0 && buf[bufLength-1] != '\n'){
            buf[bufLength] = '\n';
            bufLength++ ;
        }

        for (int i = 0; i < bufLength; i++){
            if (buf[i] == '\n'){
                
                lineCount += 1;

                line[lineip] = buf[i];
                line[lineip+1] = '\0';

                strip(line);
                split(&strSplitRes, line, " ");
                
                if (pcdinfo->isCompressed){
                    for (uint8 j = float32Start; j<float32End; j++){
                        indexNum = index[j];
                        float32Num = (float32) atof(strSplitRes.res[indexNum]);
                        bufIp = bufsIp * 4;
                        datas[j]->buf[bufIp] = *float32Numbuf0;
                        datas[j]->buf[bufIp+1] = *float32Numbuf1;
                        datas[j]->buf[bufIp+2] = *float32Numbuf2;
                        datas[j]->buf[bufIp+3] = *float32Numbuf3;
                    }
                    
                    for (uint8 j = uint32Start; j<uint32End; j++){
                        indexNum = index[j];
                        uint32Num = (uint32) atoi(strSplitRes.res[indexNum]);
                        bufIp = bufsIp * 4;
                        datas[j]->buf[bufIp] = *uint32Numbuf0;
                        datas[j]->buf[bufIp+1] = *uint32Numbuf1;
                        datas[j]->buf[bufIp+2] = *uint32Numbuf2;
                        datas[j]->buf[bufIp+3] = *uint32Numbuf3;
                    }

                    for (uint8 j = uint8Start; j<uint8End; j++){
                        indexNum = index[j];
                        uint8Num = (uint8) atoi(strSplitRes.res[indexNum]);
                        bufIp = bufsIp;
                        datas[j]->buf[bufIp] = *uint8Numbuf;
                    }

                    strSplitResFree(&strSplitRes);
                    lineip = 0;
                    bufsIp += 1;
                    if (bufsIp == len){
                        bufsIp = 0;
                        for (uint8 j = 0; j<pcdinfo->fieldCount; j++){
                            datas[j] = datas[j]->nextData;
                        }
                    }
                }else{
                    for (uint8 j = float32Start; j<float32End; j++){
                        indexNum = index[j];
                        float32Num = (float32) atof(strSplitRes.res[indexNum]);
                        
                        nowData->resbuf[binaryBufIp++] =  *float32Numbuf0;
                        nowData->resbuf[binaryBufIp++] =  *float32Numbuf1;
                        nowData->resbuf[binaryBufIp++] =  *float32Numbuf2;
                        nowData->resbuf[binaryBufIp++] =  *float32Numbuf3;
                    }
                    
                    for (uint8 j = uint32Start; j<uint32End; j++){
                        indexNum = index[j];
                        uint32Num = (uint32) atoi(strSplitRes.res[indexNum]);
                        
                        nowData->resbuf[binaryBufIp++] =  *uint32Numbuf0;
                        nowData->resbuf[binaryBufIp++] =  *uint32Numbuf1;
                        nowData->resbuf[binaryBufIp++] =  *uint32Numbuf2;
                        nowData->resbuf[binaryBufIp++] =  *uint32Numbuf3;
                    }

                    for (uint8 j = uint8Start; j<uint8End; j++){
                        indexNum = index[j];
                        uint8Num = (uint8) atoi(strSplitRes.res[indexNum]);
                        nowData->resbuf[binaryBufIp++] =  *uint8Numbuf;
                    }
                    
                    strSplitResFree(&strSplitRes);
                    
                    lineip = 0;
                    if (binaryBufIp == nowData->resbuflen){
                        binaryBufIp = 0;
                        nowData = nowData->nextData;
                    }

                }
                
            }else{
                line[lineip] = buf[i];
                lineip++;
            }
        }

        free(buf);
        buf = NULL;

    }
    
    if (lineCount != pcdinfo->pointCount){
        printf("PCD ascii line error %d/%d\n",lineCount,pcdinfo->pointCount);
        exit(1);
    }

    free(datas);
    datas = NULL;

    free(index);
    index = NULL;
}

void readPcdDataBinary(struct PcdInfo *pcdinfo, FILE *fp){
    int pcdHeadLength,pcdFileLength,dataLength,bufLength;
    char *buf = NULL;

    pcdHeadLength = ftell(fp);

    fseek(fp, 0, SEEK_END);
    pcdFileLength = ftell(fp);

    fseek(fp, pcdHeadLength, SEEK_SET);
    
    dataLength = pcdFileLength-pcdHeadLength;

    struct Data **datas = NULL;
    datas = (struct Data **) malloc (pcdinfo->fieldCount * sizeof(struct Data *));
    if (datas == NULL){
        printf("memory error\n");
        exit(1);
    }
    int32 *index = NULL;
    index = (int32 *) malloc (pcdinfo->fieldCount * sizeof(int32));
    if (index == NULL){
        printf("memory error\n");
        exit(1);
    }

    for (int i = 0; i < pcdinfo->fieldCount; i++){
        datas[i] = &(pcdinfo->fields[i]->data);
        index[i] = pcdinfo->fields[i]->index;
    }

    int32 binaryBufIp = 0;
    struct Data *nowData = &(pcdinfo->data);

    if (dataLength < pcdinfo->bufLen){
        printf("pcd binary error\n");
        exit(1);
    }
    dataLength = pcdinfo->bufLen;

    while (dataLength > 0){
        if (dataLength <= BLOCKPOINTCOUNT * pcdinfo->offset){
            bufLength = dataLength;
            dataLength = 0;
        }else{
            bufLength = BLOCKPOINTCOUNT * pcdinfo->offset;
            dataLength -= bufLength;
        }
        buf = NULL;
        buf = (char *)malloc((bufLength + 1) * sizeof(char));
        if (buf == NULL){
            printf("memory error\n");
            exit(1);
        }
        fread(buf, 1, bufLength, fp);
        if(pcdinfo->isCompressed){
            for (int i=0; i<bufLength/pcdinfo->offset;i++){
                for (uint8 j = 0; j<pcdinfo->fieldCount; j++){
                    for(uint8 k = 0; k <pcdinfo->fields[j]->size; k++){
                        datas[j]->buf[i*pcdinfo->fields[j]->size+k] = buf[i*pcdinfo->offset+pcdinfo->fields[j]->offset+k];
                    }
                }
            }
            for (uint8 i = 0; i<pcdinfo->fieldCount; i++){
                datas[i] = datas[i]->nextData;
            }
        }else{
            for (int i=0; i<bufLength/pcdinfo->offset;i++){
                for (uint8 j = 0; j<pcdinfo->fieldCount; j++){
                    for(uint8 k = 0; k <pcdinfo->fields[j]->size; k++){
                        nowData->resbuf[binaryBufIp++] = buf[i*pcdinfo->offset+pcdinfo->fields[j]->offset+k];
                    }
                }
            }
            nowData = nowData->nextData;
            binaryBufIp = 0;
        }

        free(buf);
        buf = NULL;
    }

    free(datas);
    datas = NULL;

    free(index);
    index = NULL;
}

void readPcdDataBinaryCompressed(struct PcdInfo *pcdinfo, FILE *fp){
    uint32 compressedSize, uncompressedSize;
    fread(&compressedSize, 1, 4, fp);
    fread(&uncompressedSize, 1, 4, fp);
    
    if (uncompressedSize != pcdinfo->pointCount * pcdinfo->offset){
        printf("uncompress size error\n");
        exit(1);
    }
    
    
    char *buf = NULL;
    buf = (char *)malloc((compressedSize) * sizeof(char));
    if (buf == NULL){
        printf("memory error\n");
        exit(1);
    }

    char *uncompressedBuf = NULL;
    uncompressedBuf = (char *)malloc((uncompressedSize) * sizeof(char));
    if (uncompressedBuf == NULL){
        printf("memory error\n");
        exit(1);
    }

    fread(buf, 1, compressedSize, fp);

    int err;
    unsigned int decompressSize;
    decompressSize = lzf_decompress(buf, compressedSize, uncompressedBuf, uncompressedSize, &err);
    if (decompressSize != uncompressedSize){
        printf("uncompress error\n");
        exit(1);
    }

    free(buf);
    buf = NULL;

    struct Data **datas = NULL;
    datas = (struct Data **) malloc (pcdinfo->fieldCount * sizeof(struct Data *));
    if (datas == NULL){
        printf("memory error\n");
        exit(1);
    }

    for (int i = 0; i < pcdinfo->fieldCount; i++){
        datas[i] = &(pcdinfo->fields[i]->data);
    }

    struct Data *nowData;
    uint32 ip, filedOffset;
    if (pcdinfo->isCompressed){
        for (int i = 0; i < pcdinfo->fieldCount; i++){
            nowData = datas[i];
            ip = 0;
            filedOffset = pcdinfo->fields[i]->offset * pcdinfo->pointCount;
            while (nowData != NULL){
                for (int j=0; j < nowData->len * pcdinfo->fields[i]->size; j++){
                   nowData->buf[j] = uncompressedBuf[filedOffset + ip];
                   ip++ ;
                }
                nowData = nowData->nextData;
            }
        }
    }else{
        nowData = &(pcdinfo->data);
        int pointindex = 0;
        ip = 0;
        while (nowData != NULL){
            for (int i=0; i<nowData->resbuflen / pcdinfo->aPointSize; i++){
                for (int j = 0; j < pcdinfo->fieldCount; j++){
                    filedOffset = pcdinfo->fields[j]->offset * pcdinfo->pointCount;
                    for (int k=0; k<pcdinfo->fields[j]->size; k++){
                        nowData->resbuf[ip] = uncompressedBuf[filedOffset + pointindex * pcdinfo->fields[j]->size +k];
                        ip++;
                    }
                }
                pointindex++;
            }
            nowData = nowData->nextData;
            ip = 0;
        }
        
    }
    
    free(uncompressedBuf);
    uncompressedBuf = NULL;

    free(datas);
    datas = NULL;
}

void readPcdData(struct PcdInfo *pcdinfo, FILE *fp){
    if (pcdinfo->type == ascii){
        readPcdDataAscii(pcdinfo, fp);
    }else if (pcdinfo->type == binary){
        readPcdDataBinary(pcdinfo, fp);
    }else if(pcdinfo->type == binary_compressed){
        readPcdDataBinaryCompressed(pcdinfo, fp);
    }else{
        printf("read pcd type error\n");
        exit(1);
    }
}

void writePcdHead(struct PcdInfo *pcdinfo, FILE *fp){

    char head[1000];
    char pointcountStr[20];
    sprintf(pointcountStr, "%d", pcdinfo->pointCount);
    strcpy(head, "VERSION 0.7\n");
    strcat(head, "FIELDS");
    for(uint8 i=0;i<pcdinfo->fieldCount;i++){
        strcat(head, " ");
        strcat(head, pcdinfo->fields[i]->name);
    }
    strcat(head, "\n");

    strcat(head, "SIZE");
    for(uint8 i=0;i<pcdinfo->fieldCount;i++){
        strcat(head, " ");
        if (pcdinfo->fields[i]->size == 4){
            strcat(head, "4");
        }else{
            strcat(head, "1");
        }
    }
    strcat(head, "\n");

    strcat(head, "TYPE");
    for(uint8 i=0;i<pcdinfo->fieldCount;i++){
        strcat(head, " ");
        strcat(head, pcdinfo->fields[i]->type);
    }
    strcat(head, "\n");

    strcat(head, "COUNT");
    for(uint8 i=0;i<pcdinfo->fieldCount;i++){
        strcat(head, " 1");
    }
    strcat(head, "\n");

    strcat(head, "WIDTH");
    strcat(head, " ");
    strcat(head,pointcountStr);
    strcat(head, "\n");

    strcat(head, "HEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n");

    strcat(head, "POINTS");
    strcat(head, " ");
    strcat(head,pointcountStr);
    // strcat(head, "\nDATA binary_compressed\n");
    if (pcdinfo->isCompressed){
        strcat(head, "\nDATA binary_compressed\n");
    }else{
        strcat(head, "\nDATA binary\n");
    }
    
    fputs(head, fp);
}

void writePcdData(struct PcdInfo *pcdinfo, FILE *fp){
    if (pcdinfo->isCompressed){
        uint32 databuflen,resbuflen, returnbuflen, alldatabuflen, allreturnbuflen, *pointerUint32;
        struct Data *nowData = NULL;
        struct Data *nextData = NULL;
        alldatabuflen = 0;
        allreturnbuflen = 0;
        for (int i=0; i<pcdinfo->fieldCount; i++){
            nowData = &(pcdinfo->fields[i]->data);

            databuflen = nowData->len * pcdinfo->fields[i]->size;
            resbuflen = databuflen + 1000000;
            nowData->resbuf = NULL;
            nowData->resbuf = (char *) malloc(resbuflen*sizeof(char));
            if (nowData->resbuf == NULL){
                printf("memory error\n");
                exit(1);
            }

            nowData->resbuflen = lzf_compress(nowData->buf, databuflen, nowData->resbuf, resbuflen);
            alldatabuflen += databuflen;
            allreturnbuflen += nowData->resbuflen ;

            nextData = nowData->nextData;
            nowData = nextData;



            while (nowData != NULL){
                databuflen = nowData->len * pcdinfo->fields[i]->size;
                resbuflen = databuflen + 1000000;
                nowData->resbuf = NULL;
                nowData->resbuf = (char *) malloc(resbuflen*sizeof(char));
                if (nowData->resbuf == NULL){
                    printf("memory error1\n");
                    exit(1);
                }
                nowData->resbuflen = lzf_compress(nowData->buf, databuflen, nowData->resbuf, resbuflen);
                alldatabuflen += databuflen;
                allreturnbuflen += nowData->resbuflen ;

                nextData = nowData->nextData;
                nowData = nextData;
            }

            nowData = NULL;
            nextData = NULL;
        }

        pointerUint32 = &allreturnbuflen;
        fwrite(pointerUint32, 4, 1, fp);
        pointerUint32 = &alldatabuflen;
        fwrite(pointerUint32, 4, 1, fp);

        // printf("%u  %u\n",alldatabuflen, allreturnbuflen);

        for (int i=0; i<pcdinfo->fieldCount; i++){
            nowData = &(pcdinfo->fields[i]->data);

            fwrite(nowData->resbuf, 1, nowData->resbuflen, fp);
            nextData = nowData->nextData;
            nowData = nextData;



            while (nowData != NULL){
                fwrite(nowData->resbuf, 1, nowData->resbuflen, fp);
                nextData = nowData->nextData;
                nowData = nextData;
            }

            nowData = NULL;
            nextData = NULL;
        }
    }else{
        struct Data *nowData = &(pcdinfo->data);
        while (nowData != NULL){
            fwrite(nowData->resbuf, 1, nowData->resbuflen, fp);
            nowData = nowData->nextData;
        }
    }
    
}

void writePcdTail(FILE *fp){
    char tailChar[] = {0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08, 0x00};
    fwrite(tailChar, 1, 9, fp);
}

bool rightWrite(char * filePath){
    if(access(filePath, 0) != 0){
        return false;
    }

    size_t size;
    FILE *fp = NULL;
    char buf[9];
    char tailChar[] = {0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08, 0x00};
    fp = fopen(filePath, "rb");
    if(fp == NULL){
        printf("文件读取错误\n");
        exit(-1);
    }
    fseek(fp, 0, SEEK_END);
    size = ftell(fp);
    if(size < 9){
        fclose(fp);
        return false;
    }

    fseek(fp, -9, SEEK_END);
    fread(buf, 1, 9, fp);
    if(strcmp(buf, tailChar) != 0){
        fclose(fp);
        return false;
    }

    fclose(fp);
    return true;
}

void myPrint(char* str){
    unsigned char * str_ = (unsigned char *) str;
    while (*str_ != 0)
    {
        printf("%u,",*str_);
        str_++;
    }
    printf("\n");
    
}

// solve the bug in windows
char * myDirname_(char *path){
    char tail[] = "jjjjjjjjjj";
    char * pathTemp = NULL;
    size_t pathLen, pathTempLen, tailLen, dirnameTempLen;
    char * dirnameTemp;
    pathLen = strlen(path);
    tailLen = strlen(tail);
    pathTempLen = pathLen + tailLen + 1;
    pathTemp = (char *) malloc(pathTempLen);
    if (pathTemp == NULL){
        printf("memory error\n");
        exit(-1);
    }
    memset(pathTemp, '\0', pathTempLen);
    strcpy(pathTemp, path);
    strcat(pathTemp, tail);
    dirnameTemp = dirname(pathTemp);
    dirnameTempLen = strlen(dirnameTemp);
    for (size_t i = 0; i < pathTempLen-dirnameTempLen; i++) {
        pathTemp[dirnameTempLen+i] = '\0';
    }
    if (pathTemp[dirnameTempLen-1] == '/'){
        pathTemp[dirnameTempLen-1] = '\0';
    }
    return pathTemp;
}

char * myDirname(char *path){
    char *pathTemp = NULL;
    char *dirnameTemp = NULL;
    char *dirname_ = NULL;
    size_t spaceLen;
    
    spaceLen = sizeof(char) * strlen(path) + 1;
    pathTemp = (char *)malloc(spaceLen);
    if (pathTemp == NULL){
        printf("memory error\n");
        exit(-1);
    }
    memset(pathTemp, '\0', spaceLen);
    strcpy(pathTemp, path);

    dirname_ = myDirname_(pathTemp);
    spaceLen = sizeof(char) * strlen(dirname_) + 1;
    dirnameTemp = (char *)malloc(spaceLen);
    if (dirnameTemp == NULL){
        printf("memory error\n");
        exit(-1);
    }
    memset(dirnameTemp, '\0', spaceLen);

    strcpy(dirnameTemp,dirname_);

    free(pathTemp);
    free(dirname_);
    pathTemp = NULL;

    return dirnameTemp;
}

char * myBasename(char *path){
    char *basenameTemp = NULL;
    size_t spaceLen, dirnameLen;
    char *dirname_;

    dirname_ = myDirname(path);
    dirnameLen = strlen(dirname_);
    spaceLen = strlen(path) - strlen(dirname_);
    free(dirname_);
    dirname_ = NULL;
    basenameTemp = (char *) malloc(spaceLen);
    memset(basenameTemp, '\0', spaceLen);
    for (size_t i = 0; i < spaceLen; i++){
        basenameTemp[i] = path[dirnameLen + i + 1];
    }
    return basenameTemp;
    
}

int myMkdir(char *dir){
    
    if (access(dir, 0) == 0){
        return 0;
    }

    char * pDir = NULL;

    pDir = myDirname(dir);

    if (access(pDir, 0) !=0){
        if(myMkdir(pDir) < 0){
            return -1;
        }
    }

    free(pDir);
    pDir = NULL;
  
    if(mkdir(dir) < 0){
        return -1;
    }
    
    return 0;
}

void pcdFileChange(char * pcdPath, bool forceCompressed, char *distPcdPath){
    struct PcdInfo pcdinfo;
    char * distPcdRoot;
    FILE *fp;
    int asdf;
    fp = fopen(pcdPath, "rb");
    readPcdHead(&pcdinfo, fp, forceCompressed);
    checkPcdInfo(&pcdinfo);
    
    if(pcdinfo.type == binary && pcdinfo.isChange == false && pcdinfo.isCompressed == false){
        destroyMemoryPcdInfo(&pcdinfo);
        fclose(fp);
    }else if(pcdinfo.type == binary_compressed && pcdinfo.isChange == false && pcdinfo.isCompressed == true){
        destroyMemoryPcdInfo(&pcdinfo);
        fclose(fp);
    }else{
        
        allocateMemoryPcdInfo(&pcdinfo);
        readPcdData(&pcdinfo, fp);
        fclose(fp);
        
        distPcdRoot = myDirname(distPcdPath);

        myMkdir(distPcdRoot);
        
        free(distPcdRoot);
        distPcdRoot = NULL;
        
        fp = fopen(distPcdPath, "wb");

        writePcdHead(&pcdinfo, fp);
        writePcdData(&pcdinfo, fp);
        writePcdTail(fp);
        fclose(fp);
        destroyMemoryPcdInfo(&pcdinfo);
    }
}

int getFileType(char *file){
    struct stat statbuf;

    if(stat(file,&statbuf)==-1){
		return(-1);
	}
	if(S_ISDIR(statbuf.st_mode)){
        return(1);
    }
	if(S_ISREG(statbuf.st_mode)){
        return(0);
    }
    return -1;
}

struct File{
    char *name;
    struct File *next;
};

struct File * getFile(char *srcDir, struct File *file){
    DIR *dirp;
    struct dirent *direntp;
    dirp=opendir(srcDir);
    if(dirp==NULL){
		printf("目录错误\n");
		exit(1);
	}
    direntp=readdir(dirp);
    char dirbuf[1024];
    
    while (direntp != NULL){
        memset(dirbuf,0,512);
        strcpy(dirbuf,srcDir);
        strcat(dirbuf,"/");
        strcat(dirbuf, direntp->d_name);

        if (strcmp(direntp->d_name,".")==0||strcmp(direntp->d_name,"..")==0){
            direntp=readdir(dirp);
            continue;
        }

        if (getFileType(dirbuf)==0){
            file->name = NULL;
            file->name = (char *) malloc((strlen(dirbuf) + 1) * sizeof(char));
            if (file->name == NULL){
                printf("memory error\n");
                exit(1);
            }
            memset(file->name,0,strlen(dirbuf) + 1);
            strcpy(file->name,dirbuf);
            file->next = NULL;
            file->next = (struct File *) malloc(sizeof(struct File));
            if (file->next == NULL){
                printf("memory error\n");
                exit(0);
            }
            file->next->name = NULL;
            file->next->next = NULL;
            file = file->next;
        }else if (getFileType(dirbuf)==1){
            file = getFile(dirbuf, file);
        }else{
            printf("%s dirrectory error\n",dirbuf);
            exit(0);
        }
        direntp=readdir(dirp);
    }
    closedir(dirp);
    return file;
}

void freeFile(struct File *file){
    struct File *nextFile;
    
    free(file->name);
    file->name = NULL;
    
    nextFile = file->next;
    while (nextFile != NULL){
        
        free(nextFile->name);
        nextFile->name = NULL;
        
        file = nextFile;
        nextFile = nextFile->next;
    
        free(file);
        file = NULL;
    }
}

void getPcdfile(char *completePath, char *headPath, char *pcdfile){
    int headPathLen = strlen(headPath);
    int completePathLen = strlen(completePath);
    for (int i=headPathLen+1; i<=completePathLen; i++){
        pcdfile[i-headPathLen-1] = completePath[i];
    }
}

void saveRes(char *resSaveFile){
    FILE *fp;

    fp = fopen(resSaveFile, "wb");
    fputs("1", fp);
    fclose(fp);

}

void start(char *startDir, char *resSaveFile, bool forceCompressed, bool debug){
    struct File file, *nowFile;
    struct StrSplitRes strSplitRes;
    char *name;
    int pcdfileCount = 0;
    char pcdfile[1000];
    char distPcdPath[1000];
    char headNameZh[] = {0Xbe,0Xab,0Xbc,0Xf2,0Xb5,0Xe3,0Xd4,0Xc6,0X0};
    

    file.name = NULL;
    file.next = NULL;

    getFile(startDir, &file);

    char *dataName = myBasename(startDir);
    
    nowFile = &file;
    while (nowFile->name != NULL){

        split(&strSplitRes, nowFile->name, "/");
        name = strSplitRes.res[strSplitRes.total-1];
        if (!startwith(name,".") && endwith(name, ".pcd") && !strcmp(dataName, strSplitRes.res[strSplitRes.total-4])){
            pcdfileCount += 1;
        }
        strSplitResFree(&strSplitRes);
        nowFile = nowFile->next;
    }

    nowFile = &file;
    int nowPcdfileCount = 0;

    while (nowFile->name != NULL){

        split(&strSplitRes, nowFile->name, "/");
        name = strSplitRes.res[strSplitRes.total-1];
        if (!startwith(name,".") && endwith(name, ".pcd") && !strcmp(dataName, strSplitRes.res[strSplitRes.total-4])){
            nowPcdfileCount++;
            getPcdfile(nowFile->name, startDir, pcdfile);
            if (debug){
                printf("%s: %d/%d %s/%s",headNameZh , nowPcdfileCount, pcdfileCount, dataName, pcdfile);
            }
            memset(distPcdPath, '\0', 1000);
            strcpy(distPcdPath, startDir);
            strcat(distPcdPath, PCD_S_ROOT);
            strcat(distPcdPath, pcdfile);
            if(rightWrite(distPcdPath)){
                if (debug){
                    printf(" already exists\n");
                }
                strSplitResFree(&strSplitRes);
                nowFile = nowFile->next;
                continue;
            }else{
                if (debug){
                    printf("\n");
                }
            }
            pcdFileChange(nowFile->name, forceCompressed, distPcdPath);
        }
        strSplitResFree(&strSplitRes);
        nowFile = nowFile->next;
    }
    free(dataName);
    dataName = NULL;

    freeFile(&file);
    saveRes(resSaveFile);
}

void testType(){
    uint8 u8;
    if (sizeof(u8) != 1){
        printf("uint8 定义错误\n");
        exit(1);
    }
    uint16 u16;
    if (sizeof(u16) != 2){
        printf("uint16 定义错误\n");
        exit(1);
    }
    uint32 u32;
    if (sizeof(u32) != 4){
        printf("uint32 定义错误\n");
        exit(1);
    }
    uint64 u64;
    if (sizeof(u64) != 8){
        printf("uint64 定义错误\n");
        exit(1);
    }

    int8 i8;
    if (sizeof(i8) != 1){
        printf("int8 定义错误\n");
        exit(1);
    }
    int16 i16;
    if (sizeof(i16) != 2){
        printf("int16 定义错误\n");
        exit(1);
    }
    int32 i32;
    if (sizeof(i32) != 4){
        printf("int32 定义错误\n");
        exit(1);
    }
    int64 i64;
    if (sizeof(i64) != 8){
        printf("int64 定义错误\n");
        exit(1);
    }
    float32 f32;
    if (sizeof(f32) != 4){
        printf("float32 定义错误\n");
        exit(1);
    }
    float64 f64;
    if (sizeof(f64) != 8){
        printf("float64 定义错误\n");
        exit(1);
    }

}

int main(int argc, char *argv[]) {
    testType();

    SetConsoleOutputCP(936);
    // setlocale();

    char *startDir;
    char *resSaveFile;
    bool forceCompressed, debug;

    if (argc == 4){
        printf("args error: Please input the pcd directory , resSaveFile, isCompressed, isDebug\n");
        exit(1);
    }

    if (atoi(argv[3]) == 1){
        forceCompressed = true;
    }else{
        forceCompressed = false;
    }

    if (atoi(argv[4]) == 1){
        debug = true;
    }else{
        debug = false;
    }
    
    startDir = argv[1];
    resSaveFile = argv[2];

    start(startDir, resSaveFile, forceCompressed, debug);

    return 0;
}