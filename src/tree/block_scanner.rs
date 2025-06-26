use futures::future::Future;
use futures::stream::{self, Stream};

/// Dummy result type used by the block scanner
pub type WorldTreeResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Log entry produced by the scanner
#[derive(Debug)]
pub struct Log;

pub struct BlockScanner;

impl BlockScanner {
    /// Return a stream of futures that resolve to vectors of logs.
    ///
    /// This example simply returns an empty stream. In a real implementation,
    /// each item of the stream would be a future that fetches and processes
    /// blocks.
    pub fn block_stream(
        &self,
    ) -> impl Stream<Item = impl Future<Output = WorldTreeResult<Vec<Log>>> + Send> + '_ {
        stream::empty()
    }
}
