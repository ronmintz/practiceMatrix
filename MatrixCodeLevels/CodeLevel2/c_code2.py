from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    int initCommonNeuralNet(void);
    char *runCommonNeuralNet(char *instring);
""")

ffibuilder.set_source("_c_code2",
r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <lens.h>
#include <util.h>
#include <network.h>

#define N_INPUTS  45
#define N_HIDDEN 100
#define N_OUTPUTS 10
#define CMDLEN    1024
#define LEARNING_RATE 0.05
#define MOMENTUM  0.9

// N_OUTPUTS must be the number of event types

char *event_type[N_OUTPUTS] = { "CreateEvent",
                                "DeleteEvent",
                                "ForkEvent",
                                "IssuesEvent",
                                "PullRequestEvent",
                                "PushEvent",
                                "WatchEvent",
                                "IssueCommentEvent",
                                "PullRequestReviewCommentEvent",
                                "CommitCommentEvent"};

void createNullExampleSet(void)
{
  // uses fixed example set name: train
  // for initialization, must be followed by call on overwriteExample
  int i, pos ;
  char cmd[CMDLEN];

  pos = sprintf(cmd, "loadExamples \"|echo \\\"I: ");
  for (i = 0 ; i < N_INPUTS  ; i++)
  {
     pos += sprintf(cmd+pos, "0 ");
  }

  pos += sprintf(cmd+pos, " T: ");
  for (i = 0 ; i < N_OUTPUTS  ; i++)
  {
      pos += sprintf(cmd+pos, "0 ");
  }

  sprintf(cmd+pos, ";\\\"\" -s train -mode REPLACE\n");
  lens(cmd);
}

// dcp
void overwriteExample(real *inputs, real *targets)
{
  // will overwrite first event of first example of current training set
  int i ;
  real *exInputs  = Net->trainingSet->firstExample->event->input->val ;
  real *exTargets = Net->trainingSet->firstExample->event->target->val ;

  for (i = 0 ; i < N_INPUTS  ; i++) exInputs[i] = inputs[i] ;
  for (i = 0 ; i < N_OUTPUTS ; i++) exTargets[i] = targets[i] ;
}


// stringToArray converts a string of decimal numbers separated by spaces
// to an array of these numbers.  lim = size of array.
void stringToArray(char *s, real *array, int lim)
{
    int i = 0;
    int n;

//  printf("stringToArray(%s) = \n", s);

    while ((sscanf(s, "%f %n", &array[i], &n) == 1) && (i < lim - 1))
    {
        s += n;
        i++;
    }

//  for (i = 0; i < lim; i++)
//      printf("%f\n", array[i]);

}

// createRandomArray sets each array element independently to a uniformly
// distributed random number between 0 and 1.
void createRandomArray(real *array, int len)
{
    int i;

    for (i = 0; i < len; i++)
        array[i] = drand48();
}


int initCommonNeuralNet(void)
{
    if (startLens("common_neural_net", 1))
    {
        fprintf(stderr, "Lens Failed\n");
        exit(1);
    }

    lens("verbosity 0");
    lens("addNet common_net %d %d %d", N_INPUTS, N_HIDDEN, N_OUTPUTS);
    lens("setObj learningRate %f", LEARNING_RATE);
    lens("setObj momentum %f", MOMENTUM);
    lens("setObj batchSize 1"); // DO WE NEED THIS?
    lens("setObj reportInterval 1");  // DO WE NEED THIS?
    lens("resetNet");

    lens("loadWeights orr.2000.wt");

    createNullExampleSet();
    return 0;
}

char *runCommonNeuralNet(char *instring)
{
    int i;
    char buf[50];
    real inputs[N_INPUTS];
    real outputi, maxoutput = 0;
    int imax = 0;
    char *outs = (char *)malloc(1024); // this space is not freed because it returns data to python

//    printf("instring: %s\n", instring);

//    lens("useNet common_net"); // only one net

    if (strlen(instring) == 0)
        createRandomArray(inputs, N_INPUTS);
    else
        stringToArray(instring, inputs, N_INPUTS);

    createNullExampleSet();
    overwriteExample(inputs, inputs); // only the first N_OUTPUTS components
    lens("train 1");                  // are used for targets
//    printf("after train 1\n");

//    printf("in:   ");
//    for (i = 0; i < N_INPUTS; i++) printf("%.3f ", Net->input[i]->output) ;

//    printf("\nout:  ");

    for (i = 0; i < N_OUTPUTS; i++)
    {
        outputi = Net->output[i]->output;

        if (i == 0)
        {
            maxoutput = outputi;
            imax = 0;
        }
        else
        {
            if (outputi > maxoutput)
            {
                maxoutput = outputi;
                imax = i;
            }
        }

//        printf("%.3f ", outputi);
    }

//    printf("\n");
    strcpy(outs, event_type[imax]);
    strcat(outs, ":"); // separator for use by Python

    for (i = 0; i < N_OUTPUTS; i++)
    {
        sprintf(buf, "%.3f ", Net->output[i]->output) ;
        strcat(outs, buf);
    }

    return outs;
}
""",
extra_compile_args = ["-I/home/ronmintz/Lens/Src", "-I/home/ronmintz/Lens/TclTk/tcl8.3.4/generic",
"-I/home/ronmintz/Lens/TclTk/tk8.3.4/generic",     "-I/home/ronmintz/Lens/TclTk/tcl8.3.4/unix",
"-I/home/ronmintz/Lens/TclTk/tk8.3.4/unix"],
extra_link_args = ["-L/home/ronmintz/Lens/Bin/x86_64-linux", "-llens2.63", "-ltk8.3", "-ltcl8.3", "-lm", "-lX11"])


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
