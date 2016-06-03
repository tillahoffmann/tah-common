from tah_common import Pipeline


class ExamplePipeline(Pipeline):
    # This command will be cached because it returns a value that evaluates to True
    def run_foo(self):
        print "Executed `foo`."
        return 'foo'

    # This command will not be cached
    def run_step1(self):
        print "Executed step 1."

    # This command will first execute step 1 because it `require`s it
    def run_step2(self):
        self.require('step1')
        print "Executed step 2."


if __name__ == '__main__':
    example = ExamplePipeline()
    example.run()
