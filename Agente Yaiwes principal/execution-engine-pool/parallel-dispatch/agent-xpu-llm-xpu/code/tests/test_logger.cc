#include "util/logging.h"

int main() {
  Logger &log = Logger::get_instance();
  log.log_to_file();

  log.debug("This is a debug message with value {}", 42);
  log.info("This is an info message with value {}", 3.14);
  log.warn("This is a warning message with value {:.2f} and {}", 2.71828,
           "abc");
  log.warn("This is a warning message with value {}", "abc");
  // log.error("This is an error message with value {}", true);

  return 0;
}